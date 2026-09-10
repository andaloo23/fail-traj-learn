"""Closed-loop evaluation of a learned actor in LIBERO.

Rebuilds the environment exactly as `record/record_rollouts.py` did (same LeRobot `LiberoEnv`, the same
initial-state protocol, the same shifted-init rejection sampling), then drives it with a small actor
instead of a VLA. The observation is rebuilt every step through the same `ObsBuilder` the offline data
went through, so there is no train/eval feature skew.

Eval initial states are drawn from a different seed block than the recorded corpus (`--seed-offset`),
so success here is generalisation to fresh layouts, not replay of the training inits.

Standalone use:
  eval_env.py --ckpt $FTL_RL/runs/<name>/final.pt --family full_shift8 --episodes 10
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np  # noqa: E402
import torch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "record"))
import common as C  # noqa: E402
from obs import ObsBuilder, ObsBuilderV2  # noqa: E402

# The recorder owns the privileged reader and the shifted-init sampler; reuse them rather than
# reimplementing, so evaluation states are drawn from the same distribution as the corpus.
from record_rollouts import PrivilegedReader, sample_shifted_init  # noqa: E402

MAX_OBJ_SLOTS = 12
MAX_FIXTURE_JOINTS = 16


def make_libero_env(suite: str, task_id: int, height: int, width: int):
    from lerobot.envs import make_env
    from lerobot.envs.configs import LiberoEnv

    cfg = LiberoEnv(
        task=suite, task_ids=[int(task_id)], observation_height=height, observation_width=width,
        camera_name_mapping={"agentview_image": "image", "robot0_eye_in_hand_image": "wrist_image"},
    )
    env_dict = make_env(cfg, n_envs=1, use_async_envs=False)
    vec = env_dict[suite][int(task_id)]
    return vec.envs[0]


_ENCODER: dict = {}


def get_encoder(encoder_tag: str, device: str):
    """Lazily build (and cache per process) the frozen encoder the obs_v2 checkpoints were trained with.

    Evaluation must run this on the GPU. Measured on the 3090: 6.3 ms per env step on CUDA against
    793 ms on one CPU thread, which is the difference between an affordable sweep and an impossible one.
    """
    key = (encoder_tag, device)
    if key not in _ENCODER:
        import encode_frames as E

        if encoder_tag != E.ENCODER_TAG:
            raise SystemExit(f"checkpoint wants encoder {encoder_tag}, encode_frames.py provides "
                             f"{E.ENCODER_TAG}")
        _ENCODER[key] = (E.FrozenVisionTower(device), E.load_language(C.RL / "features" / encoder_tag))
    return _ENCODER[key]


class ObsAdapter:
    """Builds the learner observation online under whichever spec the checkpoint was trained on.

    v1 reads privileged simulator state straight out of `PrivilegedReader`. v2 reads only the robot's
    own proprioception from it and gets the scene from the cameras, through the same frozen encoder and
    the same instruction embedding that `encode_frames.py` cached offline - so the online observation is
    the same function of the world as the offline one, which is the property `check_obs_consistency.py`
    exists to defend.
    """

    def __init__(self, spec: str, encoder_tag: str, device: str):
        self.spec = spec
        self.enc, self.lang_table = (get_encoder(encoder_tag, device) if spec == "v2" else (None, None))

    def builder(self, env, ti: int, gi: int, max_steps: int, task: str):
        if self.spec != "v2":
            return ObsBuilder(ti, gi, max_steps, n_slots=MAX_OBJ_SLOTS)
        import encode_frames as E

        self.cams = E.camera_keys(env)
        if task not in self.lang_table:
            raise SystemExit(f"no cached instruction embedding for {task!r}; re-run "
                             f"encode_frames.py --language-only")
        self.lang = self.lang_table[task]
        return ObsBuilderV2(max_steps, vis_dim=self.enc.dim, lang_dim=len(self.lang),
                            n_cameras=E.N_CAMERAS)

    def build(self, builder, priv: dict, t: int, obs_dict) -> np.ndarray:
        if self.spec != "v2":
            return builder.from_priv(priv, t)
        pix = obs_dict["pixels"]
        frames = np.stack([np.ascontiguousarray(pix[c][::-1, ::-1]) for c in self.cams])
        return builder.from_priv(priv, t, vis=self.enc(frames), lang=self.lang)

    @property
    def needs_pixels(self) -> bool:
        return self.spec == "v2"


class ActorPolicy:
    """Wraps a trained agent so the evaluator only needs `reset()` and `act(obs_vec)`."""

    def __init__(self, agent, device):
        self.agent, self.device = agent, device

    def reset(self):
        pass

    def act(self, obs_vec: np.ndarray) -> np.ndarray:
        x = torch.as_tensor(obs_vec, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.inference_mode():
            a = self.agent.act(x)[0].detach().cpu().numpy().astype(np.float32)
        return np.clip(a, -1.0, 1.0)


class ScriptedPolicy:
    """Zero-action reference: the floor a learned actor must clear."""

    def reset(self):
        pass

    def act(self, obs_vec):
        return np.zeros(7, np.float32)


def sim_state_hash(ctrl) -> str:
    """Fingerprint of the settled initial simulator state; the one thing that identifies an episode's
    layout independently of how it was addressed (seed, init_state_id, shift draw)."""
    try:
        flat = np.asarray(ctrl.get_sim_state(), np.float64)
    except Exception:  # noqa: BLE001 - provenance is best-effort, it must not break an evaluation
        return ""
    return hashlib.sha1(flat.tobytes()).hexdigest()[:16]


def rollout_task(policy, suite: str, task_id: int, n_episodes: int, init_mode: str, shift_xy: float,
                 shift_yaw_deg: float, seed: int, height: int, width: int, max_steps_override=None,
                 verbose: bool = False, init_state_offset: int = 0, adapter=None):
    """Run `n_episodes` in one task; returns a list of per-episode result dicts.

    Every episode records how its initial state was produced, because `seed` alone does not determine
    it: LIBERO's `LiberoEnv.reset` walks its stored initial states from index zero regardless of the
    seed, and only the shift draw comes from the seeded rng. `init_state_offset` addresses that base
    state explicitly, so an evaluation can be run on a block of base layouts the corpus never recorded
    (the recorded episodes used ids 0..29 per task; the sidecars carry the exact ones).
    """
    env = make_libero_env(suite, task_id, height, width)
    max_steps = int(max_steps_override or env._max_episode_steps)
    rng = np.random.default_rng(seed + 7919 + 1000 * int(task_id))
    stride = int(getattr(env, "_reset_stride", 1) or 1)
    adapter = adapter or ObsAdapter("v1", "", "cpu")
    results = []
    for ep_i in range(n_episodes):
        env.init_state_id = init_state_offset + ep_i * stride
        obs, _ = env.reset(seed=seed + ep_i)
        ctrl = env._env
        rs_env = ctrl.env
        init_states = getattr(env, "_init_states", None)  # a numpy array: test it for None, not falsiness
        n_init = max(len(init_states) if init_states is not None else 0, 1)
        init_state_id = (init_state_offset + ep_i * stride) % n_init
        shift_info, shift_tries, shift_valid = {}, 0, True
        if init_mode == "shifted":
            raw, shift_info, shift_tries, shift_valid = sample_shifted_init(
                ctrl, rs_env, rng, shift_xy, shift_yaw_deg, env.num_steps_wait, 30)
            obs = env._format_raw_obs(raw)
        priv_reader = PrivilegedReader(rs_env, MAX_OBJ_SLOTS, MAX_FIXTURE_JOINTS)
        # PrivilegedReader only consults the robosuite observation dict for objects whose root body it
        # could not resolve; when every body resolved, skipping _get_observations() saves a full camera
        # render per step and roughly halves evaluation time.
        needs_raw_obs = any(b < 0 for b in priv_reader.obj_body_ids)
        slots = list(priv_reader.obj_names)
        ti, gi = C.resolve_goal_slots(slots, priv_reader.goal_state, priv_reader.target_names)
        builder = adapter.builder(env, ti, gi, max_steps, getattr(env, "task_description", ""))
        init_hash = sim_state_hash(ctrl)
        policy.reset()

        success, step, t0 = False, 0, time.time()
        cur = obs  # the pre-step observation; obs_v2 reads its camera images out of this
        while step < max_steps:
            priv = priv_reader.read(rs_env._get_observations() if needs_raw_obs else {})
            action = policy.act(adapter.build(builder, priv, step, cur))
            cur, _, terminated, truncated, info = env.step(action)
            success = bool(info.get("is_success", False))
            step += 1
            if terminated or truncated:
                break
        results.append({
            "suite": suite, "task_id": int(task_id), "episode": ep_i, "success": success,
            "length": step, "seconds": round(time.time() - t0, 2),
            "target_object": slots[ti] if 0 <= ti < len(slots) else "",
            "seed": int(seed + ep_i), "init_state_id": int(init_state_id),
            "init_mode": init_mode, "shift_xy": float(shift_xy), "shift_yaw_deg": float(shift_yaw_deg),
            "shift_valid": bool(shift_valid), "shift_tries": int(shift_tries),
            "shift_applied": shift_info or {},  # per-object dxy / yaw, JSON-safe as the recorder writes it
            "init_state_sha1": init_hash,
        })
        if verbose:
            r = results[-1]
            print(f"    t{task_id} ep{ep_i}: {'OK ' if success else 'FAIL'} {step:3d} steps "
                  f"{r['seconds']:.1f}s", flush=True)
    env.close()
    return results


def _worker(job):
    """One task, in its own process: LIBERO is CPU-bound and single-threaded, the actor is 0.16M
    parameters, so tasks parallelise almost perfectly across cores."""
    import torch as _torch

    _torch.set_num_threads(1)
    ckpt = job.pop("ckpt")
    spec, encoder = job.pop("obs_spec", "v1"), job.pop("encoder", "")
    # obs_v2 runs an 86M vision tower every step, which is 125x slower on a CPU thread than on the GPU;
    # the actor is tiny either way, so keep them together on whichever device the encoder needs.
    dev = _torch.device("cuda" if spec == "v2" and _torch.cuda.is_available() else "cpu")
    _torch.set_num_threads(1)
    policy = ScriptedPolicy() if ckpt is None else ActorPolicy(load_agent(Path(ckpt), dev), dev)
    return rollout_task(policy, verbose=False, adapter=ObsAdapter(spec, encoder, str(dev)), **job)


def evaluate(policy, family: str, task_ids, n_episodes: int, seed: int, height: int = 128,
             width: int = 128, max_steps_override=None, verbose: bool = False,
             workers: int = 1, ckpt: str | None = None, init_state_offset: int = 0,
             obs_spec: str = "v1", encoder: str = "", adapter=None) -> dict:
    """Success rate of `policy` over `task_ids` of one dataset family, under that family init protocol.

    With `workers > 1` the tasks are run in separate processes, which need `ckpt` to rebuild the policy
    (a live agent cannot be pickled across a spawn); `policy` is then ignored.
    """
    suite, init_mode, shift_xy, shift_yaw = C.INIT_PROTOCOL[family]
    if obs_spec == "v2":
        # The cached features were produced from 256px renders. Feeding the encoder a different
        # resolution online would change the observation without changing the checkpoint, so the
        # render size is not a free knob under v2 - it is part of the observation spec.
        import encode_frames as E

        if (height, width) != (E.RENDER_SIZE, E.RENDER_SIZE):
            print(f"  obs_v2: overriding render size {height}x{width} -> "
                  f"{E.RENDER_SIZE}x{E.RENDER_SIZE} to match the cached features")
        height = width = E.RENDER_SIZE
    common = dict(suite=suite, n_episodes=n_episodes, init_mode=init_mode, shift_xy=shift_xy,
                  shift_yaw_deg=shift_yaw, seed=seed, height=height, width=width,
                  max_steps_override=max_steps_override, init_state_offset=init_state_offset)
    if workers > 1 and len(task_ids) > 1:
        import multiprocessing as mp

        jobs = [dict(ckpt=ckpt, task_id=int(t), obs_spec=obs_spec, encoder=encoder, **common)
                for t in task_ids]
        with mp.get_context("spawn").Pool(min(workers, len(jobs))) as pool:
            rows = [r for part in pool.map(_worker, jobs) for r in part]
    else:
        rows = []
        for tid in task_ids:
            rows += rollout_task(policy, task_id=int(tid), verbose=verbose, adapter=adapter, **common)
    n = len(rows)
    n_ok = sum(r["success"] for r in rows)
    per_task = {}
    for r in rows:
        k = r["task_id"]
        per_task.setdefault(k, []).append(r["success"])
    return {
        "family": family, "suite": suite, "init_mode": init_mode, "shift_xy": shift_xy,
        "shift_yaw_deg": shift_yaw, "seed": seed, "init_state_offset": init_state_offset,
        "n_episodes": n, "n_success": int(n_ok), "success_rate": (n_ok / n) if n else 0.0,
        "mean_length": float(np.mean([r["length"] for r in rows])) if rows else 0.0,
        "n_shift_fallbacks": int(sum(not r.get("shift_valid", True) for r in rows)),
        "per_task": {int(k): float(np.mean(v)) for k, v in sorted(per_task.items())},
        "episodes": rows,
    }


def load_agent(ckpt_path: Path, device):
    from agents import AgentConfig, make_agent
    from nets import Normalizer

    sd = torch.load(ckpt_path, map_location=device, weights_only=False)
    cfg = AgentConfig(**sd["agent_config"])
    norm = Normalizer(np.asarray(sd["obs_mean"], np.float32), np.asarray(sd["obs_std"], np.float32))
    agent = make_agent(sd["algo"], cfg, norm, device)
    agent.load_state_dict(sd["state"])
    agent.actor.eval()
    return agent


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ckpt", default=None, help="checkpoint from train.py; omit for the zero-action floor")
    ap.add_argument("--family", default="full_shift8", choices=sorted(C.INIT_PROTOCOL))
    ap.add_argument("--task-ids", type=int, nargs="*", default=list(range(10)))
    ap.add_argument("--episodes", type=int, default=10, help="per task")
    ap.add_argument("--seed", type=int, default=90000)
    ap.add_argument("--render-size", type=int, default=128,
                    help="offscreen render size; the actor never sees pixels, this only costs time")
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument("--out", default=None, help="write the full result json here")
    ap.add_argument("--workers", type=int, default=10, help="parallel task processes")
    ap.add_argument("--init-state-offset", type=int, default=0,
                    help="first stored LIBERO initial state to evaluate from; the corpus recorded ids "
                         "0..29 per task, so an offset past that gives base layouts it never saw")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    spec, encoder = "v1", ""
    if args.ckpt:
        sd = torch.load(args.ckpt, map_location="cpu", weights_only=False)
        spec = sd.get("obs_spec", "v2" if sd.get("spec_version") == "obs_v2" else "v1")
        encoder = sd.get("encoder", "") or ""
    device = torch.device("cuda" if (spec == "v2" or args.workers == 1) and torch.cuda.is_available()
                          else "cpu")
    policy = ScriptedPolicy() if not args.ckpt else ActorPolicy(load_agent(Path(args.ckpt), device), device)
    print(f"evaluating {'zero-action floor' if not args.ckpt else args.ckpt} on {args.family} "
          f"tasks {args.task_ids} x {args.episodes} episodes ({args.workers} workers)")
    t0 = time.time()
    res = evaluate(policy, args.family, args.task_ids, args.episodes, args.seed,
                   args.render_size, args.render_size, args.max_steps, verbose=not args.quiet,
                   workers=args.workers, ckpt=args.ckpt, init_state_offset=args.init_state_offset,
                   obs_spec=spec, encoder=encoder,
                   adapter=ObsAdapter(spec, encoder, str(device)) if args.workers <= 1 else None)
    res["wall_time_s"] = round(time.time() - t0, 1)
    res["ckpt"] = args.ckpt
    print(f"\nsuccess {res['n_success']}/{res['n_episodes']} = {res['success_rate']:.1%}  "
          f"mean length {res['mean_length']:.0f}  ({res['wall_time_s']:.0f}s)")
    print("per task: " + ", ".join(f"t{k}={v:.0%}" for k, v in res["per_task"].items()))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(res, indent=1))
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
