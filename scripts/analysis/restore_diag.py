"""Diagnose snapshot-replay divergence: restore a chunk snapshot, replay the recorded actions step by step and print
how far the simulator drifts from the logged per-frame columns; test whether the replay is deterministic (two replays
from the same restore) and whether MuJoCo's solver warm-start (qacc_warmstart, not part of the saved state) explains
the drift.

Usage: restore_diag.py <dataset_name> <episode> <chunk> [--steps N]
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.envs.libero import LiberoEnv, _get_suite

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "record"))
from record_rollouts import PrivilegedReader  # noqa: E402
from check_snapshot_restore_lib import gripper_cmd_history, restore  # noqa: E402  (fixture poses applied when the sidecar has them)

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))

ap = argparse.ArgumentParser()
ap.add_argument("dataset")
ap.add_argument("episode", type=int)
ap.add_argument("chunk", type=int)
ap.add_argument("--steps", type=int, default=10)
ap.add_argument("--prior", default="", help="EP:CHUNK of the same dataset to restore and replay 10 steps BEFORE the main test (mimics the checker, which reuses one env across episodes)")
args = ap.parse_args()

root = PROJ / "data" / args.dataset
ds = LeRobotDataset(f"fail_traj/{args.dataset}", root=root)
n_slots = int(np.prod(ds.features["priv.obj_pos"]["shape"]) // 3)
n_fix = int(np.prod(ds.features["priv.fixture_qpos"]["shape"])) if "priv.fixture_qpos" in ds.features else 16
ep = args.episode
rows_meta = [json.loads(l) for l in open(root / "episodes.jsonl") if l.strip()]
if ep == -1:  # first failed episode
    ep = next(r["episode_index"] for r in rows_meta if not r["success"])
elif ep == -2:  # first successful episode
    ep = next(r["episode_index"] for r in rows_meta if r["success"])
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
rec_gq = col("priv.gripper_qpos")
actions = col("action")
valid = col("priv.obj_valid")[0].astype(bool)
tm = np.flatnonzero(col("priv.target_mask")[0])
tslot = int(tm[0]) if len(tm) else None

suite = _get_suite(meta["suite"])
env = LiberoEnv(suite, meta["task_id"], meta["suite"], obs_type="pixels_agent_pos",
                observation_width=meta["image_hw"][1], observation_height=meta["image_hw"][0], num_steps_wait=10)
env.reset(seed=meta["seed"])
ctrl = env._env
rs_env = ctrl.env
sim = rs_env.sim
priv = PrivilegedReader(rs_env, n_slots, n_fix)
n_sub = int(round(rs_env.control_timestep / rs_env.model_timestep))
gcmd_recon = gripper_cmd_history(actions, n_sub, rs_env.robots[0].gripper.speed, env.num_steps_wait)
gcmd = gcmd_recon.copy()
if "gripper_cmd" in npz.files:
    gcmd[starts] = npz["gripper_cmd"]
k = args.chunk
f = int(starts[k])
m = min(args.steps, n - f - 1)
print(f"{args.dataset} ep {ep} chunk {k} frame {f}: task='{meta['task_language']}' success={meta['success']} "
      f"target={meta['object_slots'][tslot] if tslot is not None else None} state_dim={states.shape[1]} n_sub={n_sub}")
print(f"state layout: time 1 + qpos {sim.model.nq} + qvel {sim.model.nv} = {1 + sim.model.nq + sim.model.nv}; "
      f"na(act)={sim.model.na} nmocap={sim.model.nmocap}")
print(f"warmstart flag disabled: {bool(sim.model.opt.disableflags & (1 << 5))}")
print(f"gripper_cmd at chunk {k}: stored {gcmd[f]} reconstructed {gcmd_recon[f]} | recorded gripper_qpos at frame {f}: {rec_gq[f]} action[-1]={actions[f][-1]:+.2f}")


def replay(label, zero_warmstart=False, gc=None):
    restore(ctrl, rs_env, states[k], gcmd[f] if gc is None else gc, meta.get("fixture_body_pose"))
    if zero_warmstart:
        sim.data.qacc_warmstart[:] = 0.0
    traj = []
    print(f"-- {label}")
    for i in range(m):
        raw, _, _, _ = ctrl.step(actions[f + i])
        p = priv.read(raw)
        pos = p["priv.obj_pos"].reshape(-1, 3)
        d_obj = float(np.abs(pos[valid] - rec_pos[f + i + 1][valid]).max())
        d_eef = float(np.abs(p["priv.eef_pos"] - rec_eef[f + i + 1]).max())
        d_jp = float(np.abs(p["priv.joint_pos"] - rec_jp[f + i + 1]).max())
        d_gq = float(np.abs(p["priv.gripper_qpos"] - rec_gq[f + i + 1]).max())
        g = int(p["priv.obj_grasped"][tslot]) if tslot is not None else -1
        rg = int(rec_grasp[f + i + 1, tslot]) if tslot is not None else -1
        traj.append(np.asarray(ctrl.get_sim_state(), dtype=np.float64).copy())
        print(f"   step {i + 1:2d}: obj {d_obj:.1e} eef {d_eef:.1e} joints {d_jp:.1e} gripper_q {d_gq:.1e} grasp sim/rec {g}/{rg}")
    if k + 1 < len(starts) and m >= int(starts[k + 1]) - f:
        j = int(starts[k + 1]) - f - 1
        print(f"   next stored snapshot diff (after {j + 1} steps): {float(np.abs(traj[j] - states[k + 1]).max()):.1e}")
    return traj


if args.prior:
    pe, pc = args.prior.split(":")
    pe = int(pe)
    if pe == -1:
        pe = next(r["episode_index"] for r in rows_meta if not r["success"])
    elif pe == -2:
        pe = next(r["episode_index"] for r in rows_meta if r["success"])
    pnpz = np.load(root / "sidecar" / f"episode_{pe:06d}.npz")
    pf0 = int(ds.meta.episodes["dataset_from_index"][pe])
    pf1 = int(ds.meta.episodes["dataset_to_index"][pe])
    pacts = np.stack([np.asarray(x) for x in ds.hf_dataset.select(range(pf0, pf1))["action"]])
    pg = gripper_cmd_history(pacts, n_sub, rs_env.robots[0].gripper.speed, env.num_steps_wait)
    pstart = int(pnpz["chunk_start_frames"][int(pc)])
    restore(ctrl, rs_env, pnpz["sim_states"][int(pc)], pg[pstart])
    for i in range(10):
        ctrl.step(pacts[pstart + i])
    print(f"-- prior: replayed 10 steps of episode {pe} chunk {pc} in this env first")
t1 = replay("replay A (restore + stored gripper_cmd)")
t2 = replay("replay B (same again: determinism check)")
print(f"   A vs B max state diff: {max(float(np.abs(a - b).max()) for a, b in zip(t1, t2)):.1e}")
t3 = replay("replay C (qacc_warmstart zeroed after restore)", zero_warmstart=True)
print(f"   A vs C max state diff: {max(float(np.abs(a - b).max()) for a, b in zip(t1, t3)):.1e}")
t4 = replay("replay D (reconstructed gripper_cmd instead of stored)", gc=gcmd_recon[f])
print(f"   A vs D max state diff: {max(float(np.abs(a - b).max()) for a, b in zip(t1, t4)):.1e}")
if k > 0:
    # replay E: arrive at this chunk by simulating from the previous snapshot (natural solver warm-start), then continue
    fp = int(starts[k - 1])
    restore(ctrl, rs_env, states[k - 1], gcmd[fp])
    for i in range(f - fp):
        ctrl.step(actions[fp + i])
    d_here = float(np.abs(np.asarray(ctrl.get_sim_state(), dtype=np.float64) - states[k]).max())
    print(f"-- replay E (restore chunk {k - 1}, simulate to frame {f}: state diff vs stored snapshot {d_here:.1e}, then continue without restoring)")
    for i in range(m):
        raw, _, _, _ = ctrl.step(actions[f + i])
        p = priv.read(raw)
        pos = p["priv.obj_pos"].reshape(-1, 3)
        d_obj = float(np.abs(pos[valid] - rec_pos[f + i + 1][valid]).max())
        d_eef = float(np.abs(p["priv.eef_pos"] - rec_eef[f + i + 1]).max())
        d_jp = float(np.abs(p["priv.joint_pos"] - rec_jp[f + i + 1]).max())
        d_gq = float(np.abs(p["priv.gripper_qpos"] - rec_gq[f + i + 1]).max())
        g = int(p["priv.obj_grasped"][tslot]) if tslot is not None else -1
        rg = int(rec_grasp[f + i + 1, tslot]) if tslot is not None else -1
        print(f"   step {i + 1:2d}: obj {d_obj:.1e} eef {d_eef:.1e} joints {d_jp:.1e} gripper_q {d_gq:.1e} grasp sim/rec {g}/{rg}")
env.close()
