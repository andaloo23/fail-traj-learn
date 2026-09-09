"""Validate the sidecar MuJoCo snapshots: restore one, compare with the logged privileged columns, replay the
recorded actions for a few chunks, and check the simulator lands on the next stored snapshot.

Usage: check_snapshot_restore.py <dataset_name> [episode_index ...] [--chunks k,k,...] [--replay N]
Defaults: first failed and first successful episode; chunks 0, middle, second-to-last; replay 20 steps.
Prints one line per (episode, chunk) and a final RESTORE_OK / RESTORE_FAIL.

Two pass modes. "exact": the scene has no sampled fixtures, or the sidecar carries `fixture_body_pose` (schema
v3.2), so a restored episode must replay onto the next stored snapshot (float accumulation only). "approx": the
scene has fixtures (cabinet, rack, stove...) whose model placement LIBERO re-samples at every reset and the sidecar
predates v3.2, so the fixtures sit up to ~1.5 cm from the recording; the restore itself must still match every
logged column exactly, and the replay drift is reported but not judged (a grasp beside a displaced cabinet can slip).
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
from check_snapshot_restore_lib import gripper_cmd_history, restore  # noqa: E402

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))

ap = argparse.ArgumentParser()
ap.add_argument("dataset")
ap.add_argument("episodes", nargs="*", type=int)
ap.add_argument("--chunks", default="")
ap.add_argument("--replay", type=int, default=20)
ap.add_argument("--no-gripper-fix", action="store_true", help="restore only the MuJoCo state (shows the failure mode)")
ap.add_argument("--tol-restore", type=float, default=1e-6, help="pose diff allowed right after restore (m)")
ap.add_argument("--tol-state", type=float, default=1e-3, help="exact mode: allowed next-snapshot state diff")
ap.add_argument("--tol-approx", type=float, default=5e-2, help="approx mode: allowed object/eef drift during replay (m)")
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
n_approx = 0
for ep in eps:
    meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
    npz = np.load(root / "sidecar" / f"episode_{ep:06d}.npz")
    states, starts = npz["sim_states"], npz["chunk_start_frames"]
    fbp = meta.get("fixture_body_pose") or None
    mode = "exact" if (not meta.get("fixtures") or fbp) else "approx"
    n_approx += mode == "approx"
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
    tm = np.flatnonzero(col("priv.target_mask")[0])
    tslot = int(tm[0]) if len(tm) else None  # fixture-only goals (open a drawer, turn on the stove) have no target object

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
          f"state_dim={states.shape[1]} target={meta['object_slots'][tslot] if tslot is not None else None} "
          f"mode={mode}" + (f" (fixtures {meta.get('fixtures')} placed by LIBERO's sampler; pose not recorded)" if mode == "approx" else ""))
    for k in chunks:
        f = int(starts[k])
        raw = restore(ctrl, rs_env, states[k], None if gcmd is None else gcmd[f], fbp)
        p = priv.read(raw)
        pos = p["priv.obj_pos"].reshape(-1, 3)
        d_obj = np.abs(pos[valid] - rec_pos[f][valid]).max()
        d_eef = np.abs(p["priv.eef_pos"] - rec_eef[f]).max()
        d_jp = np.abs(p["priv.joint_pos"] - rec_jp[f]).max()
        flag_ok = tslot is None or ((int(p[GRASP_KEY][tslot]) == int(rec_grasp[f, tslot])) and (
            int(p["priv.obj_support_contact"][tslot]) == int(rec_sup[f, tslot])))
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
            if tslot is not None:
                flag_mismatch += int(int(p[GRASP_KEY][tslot]) != int(rec_grasp[f + i + 1, tslot]))
        # after exactly one chunk of replay the sim should sit on the next stored snapshot
        d_state = float("nan")
        if k + 1 < n_chunks and m >= int(starts[k + 1]) - f:
            restore(ctrl, rs_env, states[k], None if gcmd is None else gcmd[f], fbp)
            for i in range(int(starts[k + 1]) - f):
                ctrl.step(actions[f + i])
            d_state = float(np.abs(np.asarray(ctrl.get_sim_state()) - states[k + 1]).max())

        restore_ok = d_obj <= args.tol_restore and d_eef <= args.tol_restore and d_jp <= args.tol_restore and flag_ok
        if mode == "exact":
            # reproducible up to float accumulation (stiff contacts can amplify 1e-13 to ~1e-5 in qvel)
            sim_ok = bool(np.isnan(d_state) or d_state <= args.tol_state)
            ok = restore_ok and sim_ok and flag_mismatch == 0
            verdict = "ok" if ok else "FAIL"
        else:
            # pre-v3.2 fixture scene: the snapshot guarantees the state, not the replay (the fixture may sit ~1 cm off, so a
            # grasp beside a cabinet can slip within a few steps). Judge the restore; report the drift.
            ok = restore_ok
            drift_note = "" if (d_obj_replay <= args.tol_approx and d_eef_replay <= args.tol_approx) else " [replay drift > tol: fixture interaction]"
            verdict = ("ok (approx)" if ok else "FAIL (approx)") + drift_note
        all_ok &= ok
        print(f"  chunk {k:3d} frame {f:3d}: restore obj {d_obj:.1e} eef {d_eef:.1e} joints {d_jp:.1e} flags {'ok' if flag_ok else 'MISMATCH'} "
              f"img_mad {d_img:.1f} | replay {m} steps: obj {d_obj_replay:.1e} eef {d_eef_replay:.1e} grasp_flag_mismatches {flag_mismatch} "
              f"| next-snapshot diff {d_state:.1e} -> {verdict}")

if env is not None:
    env.close()
if n_approx:
    print(f"\n{n_approx} episode(s) judged in approx mode (fixture placement not recorded; sidecars predate schema v3.2)")
print("\nRESTORE_OK" if all_ok else "\nRESTORE_FAIL")
