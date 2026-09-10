"""Prove that the observation a policy sees in the simulator equals the one it was trained on.

Restores a recorded episode from its chunk-boundary MuJoCo snapshot (the machinery validated by
`analysis/check_snapshot_restore.py`), replays the recorded actions, and compares
`ObsBuilder.from_priv` at each step against `ObsBuilder.from_columns` on the recorded parquet rows.

A large error here means the closed-loop numbers are measuring a different MDP than the one the critic
was fit on, which would invalidate every result downstream.

  check_obs_consistency.py --dataset full_shift8__t0 --episodes 0 1 --steps 40
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "record"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import common as C  # noqa: E402
from build_dataset import PRIV_COLUMNS  # noqa: E402
from check_snapshot_restore_lib import gripper_cmd_history, restore  # noqa: E402
from eval_env import MAX_FIXTURE_JOINTS, MAX_OBJ_SLOTS, make_libero_env  # noqa: E402
from obs import BLOCKS, ObsBuilder  # noqa: E402
from record_rollouts import PrivilegedReader  # noqa: E402


def episode_frames(name: str, ep: int) -> pd.DataFrame:
    files = sorted(glob.glob(str(C.DATA / name / "data" / "**" / "*.parquet"), recursive=True))
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df = df[df["episode_index"] == ep].sort_values("frame_index", kind="stable").reset_index(drop=True)
    return df


def check_episode_v2(name: str, ep: int, n_steps: int, verbose: bool) -> dict:
    """The obs_v2 analogue: does the observation built online equal the one cached offline?

    obs_v2 gets the scene from the cameras through a frozen encoder, so the thing that has to agree is
    not just the feature assembly but the pixels feeding it. `encode_frames.render_episode` restores the
    chunk snapshot and replays inside the chunk; the online evaluator steps continuously. Both are run
    here from the SAME restored states so this measures the code path (render -> encode -> assemble),
    which is the part we control - simulator divergence over a long replay is measured by the v1 check
    and is a separate concern.
    """
    import encode_frames as E
    from obs import ObsBuilderV2

    env = E.open_env(name)
    enc = E.FrozenVisionTower("cuda" if torch_cuda() else "cpu")
    lang_table = E.load_language(C.RL / "features" / E.ENCODER_TAG)
    sc = C.sidecar(name, ep)
    lang = lang_table[sc["task_language"]]
    builder = ObsBuilderV2(int(sc["max_steps"]), vis_dim=enc.dim, lang_dim=len(lang),
                           n_cameras=E.N_CAMERAS)

    df = episode_frames(name, ep)
    n = min(n_steps, len(df))
    cols = {k: df[k].to_numpy()[:n] for k in PRIV_COLUMNS}

    cached = np.load(C.RL / "features" / E.ENCODER_TAG / f"{name}.npy")
    offset = 0
    for e in E.episode_ids(name):
        if e == ep:
            break
        if e not in C.dropped_episodes(name):
            offset += len(E.episode_actions(name, e))
    offline = builder.from_columns(cols, n, vis=cached[offset:offset + n].astype(np.float32), lang=lang)

    online = np.zeros_like(offline)
    for t, (f, frames) in enumerate(E.render_episode(env, name, ep, n)):
        priv = {k: np.asarray(cols[k][t]) for k in PRIV_COLUMNS}
        online[t] = builder.from_priv(priv, f, vis=enc(frames), lang=lang)
    env.close()

    err = np.abs(online - offline)
    vis_start, vis_w = 27, E.N_CAMERAS * enc.dim
    # A max over 1536 feature dimensions is not interpretable on its own. What matters is the size of
    # the disagreement against the size of the frame-to-frame signal the critic has to read: if the
    # replay noise is a fraction of the difference between neighbouring frames, it is not what limits
    # the experiment. The residual comes from robosuite's OSC controller state, which lives outside the
    # MuJoCo snapshot and so is not restored at a chunk boundary.
    on_v = online[:, vis_start:vis_start + vis_w]
    off_v = offline[:, vis_start:vis_start + vis_w]
    rel = np.linalg.norm(on_v - off_v, axis=1) / np.maximum(np.linalg.norm(off_v, axis=1), 1e-8)
    signal = np.linalg.norm(np.diff(off_v, axis=0), axis=1) / np.maximum(
        np.linalg.norm(off_v[:-1], axis=1), 1e-8)
    res = {"dataset": name, "episode": ep, "steps": n, "spec": "v2",
           "max_abs_err": float(err.max()), "mean_abs_err": float(err.mean()),
           "err_at_step0": float(err[0].max()),
           "vision_rel_err_mean": float(rel.mean()), "vision_rel_err_max": float(rel.max()),
           "adjacent_frame_rel_change": float(signal.mean()),
           "noise_to_signal": float(rel.mean() / max(signal.mean(), 1e-8)),
           "per_block_max": {"proprio": float(err[:, :27].max()),
                             "vision": float(err[:, vis_start:vis_start + vis_w].max()),
                             "language": float(err[:, vis_start + vis_w:-2].max()),
                             "time": float(err[:, -2:].max())}}
    if verbose:
        print(f"  {name} ep{ep}: {n} steps  max|err|={res['max_abs_err']:.2e}  "
              f"step0={res['err_at_step0']:.2e}")
        print("    " + "  ".join(f"{k}={v:.1e}" for k, v in res["per_block_max"].items()))
        print(f"    vision relative error {res['vision_rel_err_mean']:.4f} vs frame-to-frame change "
              f"{res['adjacent_frame_rel_change']:.4f}  (noise/signal {res['noise_to_signal']:.3f})")
    return res


def torch_cuda() -> bool:
    import torch

    return torch.cuda.is_available()


def check_episode(name: str, ep: int, n_steps: int, render_size: int, verbose: bool) -> dict:
    sc = C.sidecar(name, ep)
    snap = np.load(C.DATA / name / "sidecar" / f"episode_{ep:06d}.npz")
    df = episode_frames(name, ep)
    n = min(n_steps, len(df))
    actions = np.stack([np.asarray(a, np.float32) for a in df["action"].to_numpy()])

    suite = sc["suite"]
    env = make_libero_env(suite, int(sc["task_id"]), render_size, render_size)
    env.reset(seed=int(sc.get("seed", 0)))
    ctrl, rs_env = env._env, env._env.env
    n_sub = int(rs_env.control_timestep / rs_env.model_timestep)
    speed = float(rs_env.robots[0].gripper.speed)
    cmd_hist = gripper_cmd_history(actions, n_sub, speed, env.num_steps_wait)
    gcmd = snap["gripper_cmd"][0] if "gripper_cmd" in snap else cmd_hist[0]
    restore(ctrl, rs_env, snap["sim_states"][0], gcmd, sc.get("fixture_body_pose"))

    reader = PrivilegedReader(rs_env, MAX_OBJ_SLOTS, MAX_FIXTURE_JOINTS)
    slots = list(sc.get("object_slots", []))
    ti, gi = C.resolve_goal_slots(slots, sc.get("goal_state"), sc.get("target_objects"))
    ti_env, gi_env = C.resolve_goal_slots(list(reader.obj_names), reader.goal_state, reader.target_names)
    if (ti, gi) != (ti_env, gi_env):
        raise AssertionError(f"{name} ep{ep}: sidecar slots {(ti, gi)} != env slots {(ti_env, gi_env)}")
    builder = ObsBuilder(ti, gi, int(sc["max_steps"]), n_slots=MAX_OBJ_SLOTS)

    cols = {k: df[k].to_numpy()[:n] for k in PRIV_COLUMNS}
    offline = builder.from_columns(cols, n, t0=0)

    online = np.zeros_like(offline)
    for t in range(n):
        online[t] = builder.from_priv(reader.read(rs_env._get_observations()), t)
        env.step(actions[t])
    env.close()

    err = np.abs(online - offline)
    per_block, i = {}, 0
    for bname, w in BLOCKS:
        per_block[bname] = float(err[:, i:i + w].max())
        i += w
    worst_t = int(err.max(axis=1).argmax())
    res = {
        "dataset": name, "episode": ep, "steps": n, "max_abs_err": float(err.max()),
        "mean_abs_err": float(err.mean()), "err_at_step0": float(err[0].max()),
        "worst_step": worst_t, "per_block_max": per_block,
    }
    if verbose:
        print(f"  {name} ep{ep}: {n} steps  max|err|={res['max_abs_err']:.2e} "
              f"(step {worst_t})  step0={res['err_at_step0']:.2e}")
        print("    " + "  ".join(f"{k}={v:.1e}" for k, v in per_block.items()))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dataset", default="full_shift8__t0")
    ap.add_argument("--episodes", type=int, nargs="*", default=[0, 1, 2])
    ap.add_argument("--steps", type=int, default=40, help="replayed steps per episode")
    ap.add_argument("--render-size", type=int, default=128)
    ap.add_argument("--obs-spec", default="v1", choices=["v1", "v2"])
    ap.add_argument("--tol", type=float, default=1e-3, help="pass threshold on the step-0 error")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rows = [check_episode_v2(args.dataset, ep, args.steps, True) if args.obs_spec == "v2"
            else check_episode(args.dataset, ep, args.steps, args.render_size, True)
            for ep in args.episodes]
    step0 = max(r["err_at_step0"] for r in rows)
    drift = max(r["max_abs_err"] for r in rows)
    print(f"\nstep-0 max error {step0:.2e} (tol {args.tol:g}); "
          f"max error over the replay {drift:.2e} (grows with simulator divergence, not a bug by itself)")
    if args.out:
        Path(args.out).write_text(json.dumps(rows, indent=1))
    print("OBS_CONSISTENCY_OK" if step0 <= args.tol else "OBS_CONSISTENCY_FAIL")
    sys.exit(0 if step0 <= args.tol else 1)


if __name__ == "__main__":
    main()
