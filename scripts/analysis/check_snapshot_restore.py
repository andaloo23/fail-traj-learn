"""Validate the sidecar MuJoCo snapshots: restore one, compare with the logged privileged columns, replay the
recorded actions for a few chunks, and check the simulator lands on the next stored snapshot.

Usage: check_snapshot_restore.py <dataset_name> [episode_index ...] [--chunks k,k,...] [--replay N]
Defaults: first failed and first successful episode; chunks 0, middle, second-to-last; replay 20 steps.
Prints one line per (episode, chunk) and a final RESTORE_OK / RESTORE_FAIL.
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np
import torch

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.envs.libero import LiberoEnv, _get_suite

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "record"))
from record_rollouts import PrivilegedReader  # noqa: E402

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))


def gripper_cmd_history(actions: np.ndarray, n_sub: int, speed: float, n_wait: int) -> np.ndarray:
    """robosuite PandaGripper.format_action keeps `current_action` (not part of the MuJoCo state): every
    simulator substep it moves by [-1, 1] * speed * sign(gripper_action) and is clipped to [-1, 1]. Rebuild it
    for every frame from the LIBERO dummy wait steps (gripper -1) followed by the recorded actions.
    Returns (len(actions) + 1, 2): row f is the value in effect right before the action at frame f."""
    step = np.array([-1.0, 1.0]) * speed
    ca = np.zeros(2)
    for _ in range(n_wait * n_sub):
        ca = np.clip(ca + step * np.sign(-1.0), -1.0, 1.0)
    out = np.zeros((len(actions) + 1, 2))
    out[0] = ca
    for i, a in enumerate(actions[:, -1]):
        s = np.sign(float(a))
        for _ in range(n_sub):
            ca = np.clip(ca + step * s, -1.0, 1.0)
        out[i + 1] = ca
    return out


def restore(ctrl, rs_env, state: np.ndarray, gripper_cmd: np.ndarray | None):
    raw = ctrl.set_init_state(state)
    if gripper_cmd is not None:
        rs_env.robots[0].gripper.current_action = np.array(gripper_cmd, dtype=np.float64)
    return raw

ap = argparse.ArgumentParser()
ap.add_argument("dataset")
ap.add_argument("episodes", nargs="*", type=int)
ap.add_argument("--chunks", default="")
ap.add_argument("--replay", type=int, default=20)
ap.add_argument("--no-gripper-fix", action="store_true", help="restore only the MuJoCo state (shows the failure mode)")
ap.add_argument("--tol-restore", type=float, default=2e-3, help="informational: pose diff right after restore (m)")
ap.add_argument("--tol-replay", type=float, default=1e-2, help="informational: pose diff during replay (m)")
args = ap.parse_args()

root = PROJ / "data" / args.dataset
ds = LeRobotDataset(f"fail_traj/{args.dataset}", root=root)
n_slots = int(np.prod(ds.features["priv.obj_pos"]["shape"]) // 3)
n_fix = int(np.prod(ds.features["priv.fixture_qpos"]["shape"])) if "priv.fixture_qpos" in ds.features else 16
# schema v1 datasets logged the finger-PAD grasp rule under priv.obj_grasped; v2 keeps it as priv.obj_grasped_pads
GRASP_KEY = "priv.obj_grasped" if "priv.obj_grasped_pads" in ds.features else "priv.obj_grasped_pads"

eps = args.episodes
if not eps:
    rows = [json.loads(l) for l in open(root / "episodes.jsonl")]
    fails = [r["episode_index"] for r in rows if not r["success"]]
    succs = [r["episode_index"] for r in rows if r["success"]]
    eps = fails[:1] + succs[:1]
print(f"dataset {args.dataset}: {ds.num_episodes} episodes, checking {eps}")

env = None
cur_task = None
all_ok = True
for ep in eps:
    meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
    npz = np.load(root / "sidecar" / f"episode_{ep:06d}.npz")
    states, starts = npz["sim_states"], npz["chunk_start_frames"]
    f0 = int(ds.meta.episodes["dataset_from_index"][ep])
    f1 = int(ds.meta.episodes["dataset_to_index"][ep])
    n = f1 - f0
    cols = ds.hf_dataset.select(range(f0, f1))
    col = lambda k: np.stack([np.asarray(x) for x in cols[k]])  # noqa: E731
    rec_pos = col("priv.obj_pos").reshape(n, -1, 3)
    rec_eef = col("priv.eef_pos")
    rec_jp = col("priv.joint_pos")
    rec_grasp = col("priv.obj_grasped")
    rec_sup = col("priv.obj_support_contact")
    actions = col("action")
    valid = col("priv.obj_valid")[0].astype(bool)
    tslot = int(np.flatnonzero(col("priv.target_mask")[0])[0])

    key = (meta["suite"], meta["task_id"])
    if key != cur_task:
        if env is not None:
            env.close()
        suite = _get_suite(meta["suite"])
        env = LiberoEnv(suite, meta["task_id"], meta["suite"], obs_type="pixels_agent_pos",
                        observation_width=meta["image_hw"][1], observation_height=meta["image_hw"][0],
                        num_steps_wait=10)
        env.reset(seed=meta["seed"])
        cur_task = key
    ctrl = env._env
    rs_env = ctrl.env
    priv = PrivilegedReader(rs_env, n_slots, n_fix)
    n_sub = int(round(rs_env.control_timestep / rs_env.model_timestep))
    gcmd = None if args.no_gripper_fix else gripper_cmd_history(actions, n_sub, rs_env.robots[0].gripper.speed, env.num_steps_wait)
    if "gripper_cmd" in npz.files and gcmd is not None:
        d_g = float(np.abs(npz["gripper_cmd"] - gcmd[starts]).max())
        print(f"  stored gripper_cmd (schema v3) vs reconstruction from actions: max diff {d_g:.1e}")
        gcmd = gcmd.copy()
        gcmd[starts] = npz["gripper_cmd"]  # prefer the stored value at chunk boundaries
    assert priv.obj_names == meta["object_slots"], (priv.obj_names, meta["object_slots"])

    n_chunks = len(starts)
    chunks = [c for c in ([int(c) for c in args.chunks.split(",") if c] or sorted({0, n_chunks // 2, max(0, n_chunks - 2)})) if c < n_chunks]
    print(f"\nepisode {ep}: task={meta['task_id']} success={meta['success']} len={n} chunks={n_chunks} "
          f"state_dim={states.shape[1]} target={meta['object_slots'][tslot]}")
    for k in chunks:
        f = int(starts[k])
        raw = restore(ctrl, rs_env, states[k], None if gcmd is None else gcmd[f])
        p = priv.read(raw)
        pos = p["priv.obj_pos"].reshape(-1, 3)
        d_obj = np.abs(pos[valid] - rec_pos[f][valid]).max()
        d_eef = np.abs(p["priv.eef_pos"] - rec_eef[f]).max()
        d_jp = np.abs(p["priv.joint_pos"] - rec_jp[f]).max()
        flag_ok = (int(p[GRASP_KEY][tslot]) == int(rec_grasp[f, tslot])) and (
            int(p["priv.obj_support_contact"][tslot]) == int(rec_sup[f, tslot]))
        # image check: raw agentview rotated 180 vs decoded recorded frame
        img = np.ascontiguousarray(raw["agentview_image"][::-1, ::-1]).astype(np.float32)
        rec_img = ds[f0 + f]["observation.images.image"]
        rec_img = (rec_img.permute(1, 2, 0).numpy() * 255).astype(np.float32) if isinstance(rec_img, torch.Tensor) else np.asarray(rec_img, np.float32)
        d_img = float(np.abs(img - rec_img).mean())

        # replay recorded actions and compare against the logged pre-step columns
        m = min(args.replay, n - f - 1)
        d_obj_replay = d_eef_replay = 0.0
        flag_mismatch = 0
        for i in range(m):
            raw, _, _, _ = ctrl.step(actions[f + i])
            p = priv.read(raw)
            pos = p["priv.obj_pos"].reshape(-1, 3)
            d_obj_replay = max(d_obj_replay, float(np.abs(pos[valid] - rec_pos[f + i + 1][valid]).max()))
            d_eef_replay = max(d_eef_replay, float(np.abs(p["priv.eef_pos"] - rec_eef[f + i + 1]).max()))
            flag_mismatch += int(int(p[GRASP_KEY][tslot]) != int(rec_grasp[f + i + 1, tslot]))
        # after exactly one chunk of replay the sim should sit on the next stored snapshot
        d_state = float("nan")
        if k + 1 < n_chunks and m >= int(starts[k + 1]) - f:
            # replay covered the next boundary; re-run exactly to it for the state comparison
            restore(ctrl, rs_env, states[k], None if gcmd is None else gcmd[f])
            for i in range(int(starts[k + 1]) - f):
                ctrl.step(actions[f + i])
            d_state = float(np.abs(np.asarray(ctrl.get_sim_state()) - states[k + 1]).max())

        # Pass criterion: the simulator must be reproducible (replay reaches the next stored snapshot within float
        # accumulation) and the contact flags must agree. Pose columns are informational: robosuite observables are
        # sampled at the first substep of a control step, so logged poses lag the true state by up to one control
        # step while the arm is moving.
        sim_ok = bool(np.isnan(d_state) or d_state <= 1e-6)
        pose_ok = d_obj <= args.tol_restore and d_eef <= args.tol_restore and \
            d_obj_replay <= args.tol_replay and d_eef_replay <= args.tol_replay
        ok = sim_ok and flag_ok and flag_mismatch == 0
        all_ok &= ok
        print(f"  chunk {k:3d} frame {f:3d}: restore obj {d_obj:.1e} eef {d_eef:.1e} joints {d_jp:.1e} flags {'ok' if flag_ok else 'MISMATCH'} "
              f"img_mad {d_img:.1f} | replay {m} steps: obj {d_obj_replay:.1e} eef {d_eef_replay:.1e} grasp_flag_mismatches {flag_mismatch} "
              f"| next-snapshot diff {d_state:.1e} -> {'ok' if ok else 'FAIL'}{'' if pose_ok else ' (pose cols beyond tol: obs lag)'}")

if env is not None:
    env.close()
print("\nRESTORE_OK" if all_ok else "\nRESTORE_FAIL")
