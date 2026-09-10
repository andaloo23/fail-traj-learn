"""Flatten the recorded corpus into offline-RL transitions.

Reads the LeRobotDataset parquets plus their sidecars, builds the learner observation (`obs.py`) and
writes one directory of arrays that every trainer memory-maps:

  obs.npy        (N, OBS_DIM) float32   state at t
  next_obs.npy   (N, OBS_DIM) float32   state at t+1 (copy of obs at the last frame; masked by done)
  action.npy     (N, 7)       float32   the executed action, already in [-1, 1]
  reward.npy     (N,)         float32   1.0 on the successful terminal transition, else 0.0
  done.npy       (N,)         bool      last frame of the episode (see --bootstrap-timeout)
  timeout.npy    (N,)         bool      last frame of an episode that ended by running out of steps
  ep_id.npy      (N,)         int32     row index into episodes.parquet
  frame_index.npy(N,)         int32     step within the episode
  episodes.parquet            one row per episode: dataset, episode_index, task, success, length, ...
  meta.json                   obs spec, corpus, normalisation statistics, counts

Usage:
  build_dataset.py --corpus object --tag object_v1
  build_dataset.py --datasets full_shift8 full_shift12 --tag hard
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from obs import OBS_DIM, SPEC_VERSION, SPEC_VERSION_V2, ObsBuilder, ObsBuilderV2  # noqa: E402

PRIV_COLUMNS = [
    "priv.eef_pos", "priv.eef_quat", "priv.gripper_qpos", "priv.gripper_qvel",
    "priv.joint_pos", "priv.joint_vel", "priv.obj_pos", "priv.obj_quat", "priv.obj_valid",
    "priv.obj_gripper_contact", "priv.obj_grasped", "priv.obj_support_contact",
    "priv.n_contacts", "priv.arm_contacts", "priv.gripper_static_contacts",
    "priv.fixture_qpos", "priv.fixture_valid",
]
READ_COLUMNS = PRIV_COLUMNS + ["action", "episode_index", "frame_index", "next.success", "next.done"]


def read_dataset(name: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(C.DATA / name / "data" / "**" / "*.parquet"), recursive=True))
    if not files:
        raise FileNotFoundError(f"no data parquet under {C.DATA / name}")
    df = pd.concat([pd.read_parquet(f, columns=READ_COLUMNS) for f in files], ignore_index=True)
    return df.sort_values(["episode_index", "frame_index"], kind="stable").reset_index(drop=True)


def episode_rows(name: str):
    """Sidecar metadata per episode, with the acceptance-audit success corrections applied."""
    dropped = C.dropped_episodes(name)
    out = {}
    for p in sorted((C.DATA / name / "sidecar").glob("episode_*.json")):
        sc = json.loads(p.read_text())
        ep = int(sc["episode_index"])
        if ep in dropped:
            continue
        slots = list(sc.get("object_slots", []))
        ti, gi = C.resolve_goal_slots(slots, sc.get("goal_state"), sc.get("target_objects"))
        out[ep] = {
            "dataset": name, "episode_index": ep, "family": C.family_of(name),
            "suite": sc.get("suite", ""), "task_id": int(sc.get("task_id", C.task_id_of(name))),
            "task": sc.get("task_language", ""), "task_name": sc.get("task_name", ""),
            "success": C.corrected_success(name, ep, bool(sc.get("success", False))),
            "terminated": bool(sc.get("terminated", False)),
            "length": int(sc.get("length", 0)), "max_steps": int(sc.get("max_steps", 0)),
            "init_mode": sc.get("init_mode", "standard"), "shift_xy": float(sc.get("shift_xy", 0.0)),
            "shift_yaw_deg": float(sc.get("shift_yaw_deg", 0.0)), "seed": int(sc.get("seed", -1)),
            "target_slot": int(ti), "goal_slot": int(gi),
            "target_object": slots[ti] if 0 <= ti < len(slots) else "",
            "goal_object": slots[gi] if 0 <= gi < len(slots) else "",
            "n_slots": len(slots),
        }
    return out


def load_features(name: str, encoder: str):
    """(features, language lookup) for one dataset, or (None, None) for the privileged v1 spec.

    The feature file is written by `encode_frames.py` in exactly the order this function consumes it:
    episodes ascending, dropped episodes excluded, frames in order. The per-episode length assertion
    below is what makes that contract enforced rather than assumed - a silent misalignment would give
    every frame someone else's picture.
    """
    import encode_frames as E

    d = C.RL / "features" / encoder
    path = d / f"{name}.npy"
    if not path.exists():
        raise SystemExit(f"{path} not found - run encode_frames.py --datasets {name}")
    return np.load(path), E.load_language(d)


def build(names, bootstrap_timeout: bool, spec: str = "v1", encoder: str = ""):
    obs_parts, nobs_parts, act_parts = [], [], []
    rew_parts, done_parts, to_parts, epid_parts, fidx_parts = [], [], [], [], []
    ep_meta, ep_id = [], 0
    for name in names:
        t0 = time.time()
        df = read_dataset(name)
        metas = episode_rows(name)
        feats, lang_table = (load_features(name, encoder) if spec == "v2" else (None, None))
        cursor = 0
        n_ep = 0
        for ep, sub in df.groupby("episode_index", sort=True):
            ep = int(ep)
            if ep not in metas:
                continue
            m = metas[ep]
            n = len(sub)
            if n != m["length"]:
                # The sidecar length is authoritative for the outcome; a mismatch means a truncated write.
                print(f"  ! {name} ep{ep}: {n} frames but sidecar length {m['length']}, using frames")
                m["length"] = n
            cols = {k: sub[k].to_numpy() for k in PRIV_COLUMNS}
            if spec == "v2":
                vis = feats[cursor:cursor + n]
                if len(vis) != n:
                    raise SystemExit(f"{name} ep{ep}: {len(vis)} cached feature rows for {n} frames "
                                     f"(cursor {cursor} of {len(feats)}) - re-run encode_frames.py")
                cursor += n
                lang = lang_table[m["task"]]
                b = ObsBuilderV2(m["max_steps"] or n, vis_dim=vis.shape[-1], lang_dim=len(lang),
                                 n_cameras=vis.shape[1])
                o = b.from_columns(cols, n, vis=vis, lang=lang, t0=0)
            else:
                b = ObsBuilder(m["target_slot"], m["goal_slot"], m["max_steps"] or n, n_slots=12)
                o = b.from_columns(cols, n, t0=0)
            nxt = np.empty_like(o)
            nxt[:-1] = o[1:]
            # The recorder stores the PRE-step observation of every frame, so the state after the final
            # action was never written. With the default (done=1 at the last frame) this row is masked
            # out of the TD target and the copy is inert; under --bootstrap-timeout it is a one-step-stale
            # approximation of s_T, which is the price of not having recorded it.
            nxt[-1] = o[-1]
            act = np.stack([np.asarray(a, np.float32) for a in sub["action"].to_numpy()])
            rew = np.zeros(n, np.float32)
            if m["success"]:
                rew[-1] = 1.0
            done = np.zeros(n, bool)
            done[-1] = True
            timeout = np.zeros(n, bool)
            timeout[-1] = not m["terminated"]
            obs_parts.append(o)
            nobs_parts.append(nxt)
            act_parts.append(np.clip(act, -1.0, 1.0))
            rew_parts.append(rew)
            # With --bootstrap-timeout the critic keeps bootstrapping through a step-limit ending, so a
            # failure is "not finished yet" rather than "worth zero". Default off: the episode budget is
            # part of the task, so running out of steps IS the failure.
            done_parts.append(done & ~timeout if bootstrap_timeout else done)
            to_parts.append(timeout)
            epid_parts.append(np.full(n, ep_id, np.int32))
            fidx_parts.append(np.arange(n, dtype=np.int32))
            m["ep_id"] = ep_id
            ep_meta.append(m)
            ep_id += 1
            n_ep += 1
        if spec == "v2" and cursor != len(feats):
            raise SystemExit(f"{name}: consumed {cursor} of {len(feats)} cached feature rows")
        print(f"  {name:20s} {n_ep:4d} episodes, {len(df):7d} frames  ({time.time() - t0:.1f}s)")

    if not ep_meta:
        raise SystemExit("no episodes built")
    out = {
        "obs": np.concatenate(obs_parts), "next_obs": np.concatenate(nobs_parts),
        "action": np.concatenate(act_parts), "reward": np.concatenate(rew_parts),
        "done": np.concatenate(done_parts), "timeout": np.concatenate(to_parts),
        "ep_id": np.concatenate(epid_parts), "frame_index": np.concatenate(fidx_parts),
    }
    return out, pd.DataFrame(ep_meta)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus", default=None, help=f"one of {sorted(C.CORPUS)}")
    ap.add_argument("--datasets", nargs="*", default=None, help="dataset names or family prefixes")
    ap.add_argument("--tag", required=True, help="output directory name under $FTL_RL/datasets")
    ap.add_argument("--bootstrap-timeout", action="store_true",
                    help="treat a step-limit ending as truncation (bootstrap) instead of termination; "
                         "the final next_obs is then a one-step-stale copy, see the note in build()")
    ap.add_argument("--obs-spec", default="v1", choices=["v1", "v2"],
                    help="v1 = privileged simulator state (90d); v2 = strictly observable "
                         "(proprioception + frozen visual features + task language)")
    ap.add_argument("--encoder", default="smolvlm2_500m_siglip_256",
                    help="v2 only: feature cache under $FTL_RL/features")
    args = ap.parse_args()
    if not args.corpus and not args.datasets:
        ap.error("give --corpus or --datasets")
    names = C.expand([args.corpus] if args.corpus else args.datasets)
    print(f"building {len(names)} datasets -> tag {args.tag}")

    arrays, eps = build(names, args.bootstrap_timeout, args.obs_spec, args.encoder)
    out = C.RL / "datasets" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    for k, v in arrays.items():
        np.save(out / f"{k}.npy", v)
    eps.to_parquet(out / "episodes.parquet", index=False)

    obs = arrays["obs"]
    mean, std = obs.mean(0), obs.std(0)
    std = np.where(std < 1e-3, 1.0, std)  # constant features stay constant, they do not get amplified
    meta = {
        "spec_version": SPEC_VERSION_V2 if args.obs_spec == "v2" else SPEC_VERSION,
        "obs_spec": args.obs_spec,
        "encoder": args.encoder if args.obs_spec == "v2" else None,
        "obs_dim": int(obs.shape[1]), "action_dim": int(arrays["action"].shape[1]),
        "corpus": args.corpus, "datasets": names, "bootstrap_timeout": bool(args.bootstrap_timeout),
        "n_frames": int(len(obs)), "n_episodes": int(len(eps)),
        "n_success": int(eps["success"].sum()), "n_failure": int((~eps["success"]).sum()),
        "obs_mean": mean.tolist(), "obs_std": std.tolist(),
        "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"\n{len(obs)} transitions, {len(eps)} episodes "
          f"({meta['n_success']} success / {meta['n_failure']} failure) -> {out}")
    print(f"reward mass: {arrays['reward'].sum():.0f}   dones: {arrays['done'].sum()}   "
          f"timeouts: {arrays['timeout'].sum()}")
    print(eps.groupby("family")["success"].agg(["count", "sum", "mean"]).to_string())


if __name__ == "__main__":
    main()
