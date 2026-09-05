"""Sanity-check a recorded dataset: schema, privileged signals over time, sidecars, image orientation.

Usage: verify_dataset.py <dataset_name> [episode_index]
Writes a comparison PNG (recorded frame vs lerobot/libero demo frame) to the Windows outputs dir.
"""
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from lerobot.datasets.lerobot_dataset import LeRobotDataset

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))
WIN_OUT = Path(os.environ.get("FTL_WIN_OUT", "/mnt/c/Users/LocalPC/dev/fail-traj-learn/outputs"))

name = sys.argv[1] if len(sys.argv) > 1 else "smoke_rec"
ep = int(sys.argv[2]) if len(sys.argv) > 2 else 0
root = PROJ / "data" / name

ds = LeRobotDataset(f"fail_traj/{name}", root=root)
print(f"dataset {root}: episodes={ds.num_episodes} frames={ds.num_frames} fps={ds.fps}")
print("features:")
for k, v in ds.features.items():
    print(f"  {k:32s} {v['dtype']:8s} {v['shape']}")

# episode slice
from_idx = int(ds.meta.episodes["dataset_from_index"][ep])
to_idx = int(ds.meta.episodes["dataset_to_index"][ep])
n = to_idx - from_idx
print(f"\nepisode {ep}: frames [{from_idx}, {to_idx}) n={n} task={ds.meta.episodes['tasks'][ep]}")

# pull the non-video columns for the episode straight from the parquet-backed hf dataset
cols = ds.hf_dataset.select(range(from_idx, to_idx))
def col(k):
    return np.stack([np.asarray(x) for x in cols[k]])

succ = col("next.success").reshape(-1)
done = col("next.done").reshape(-1)
rew = col("next.reward").reshape(-1)
ci = col("chunk.index").reshape(-1)
cs = col("chunk.step").reshape(-1)
print(f"success: first True at frame {int(np.argmax(succ)) if succ.any() else -1}, last frame success={bool(succ[-1])}, done[-1]={bool(done[-1])}, reward sum={rew.sum():.1f}")
print(f"chunks: max index {ci.max()} ; chunk.step pattern ok = {bool(np.all(cs == np.arange(n) % 10))}")

valid = col("priv.obj_valid")[0]
target = col("priv.target_mask")[0]
meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
slots = meta["object_slots"]
print(f"object slots ({int(valid.sum())} valid): {slots}")
print(f"target objects: {meta['target_objects']} -> mask slots {np.flatnonzero(target).tolist()}")

grasp = col("priv.obj_grasped")
gcon = col("priv.obj_gripper_contact")
tcon = col("priv.obj_support_contact")
oocon = col("priv.obj_obj_contact")
armc = col("priv.arm_contacts").reshape(-1)
gsc = col("priv.gripper_static_contacts").reshape(-1)
pos = col("priv.obj_pos").reshape(n, -1, 3)
tslot = int(np.flatnonzero(target)[0]) if target.any() else 0
print(f"\ntarget slot {tslot} ({slots[tslot] if tslot < len(slots) else '?'}):")
print(f"  gripper contact frames: {np.flatnonzero(gcon[:, tslot]).tolist()[:5]} ... total {int(gcon[:, tslot].sum())}")
print(f"  grasped frames (priv.obj_grasped; fingers in schema v2, pads in v1): first {int(np.argmax(grasp[:, tslot])) if grasp[:, tslot].any() else -1}, total {int(grasp[:, tslot].sum())}")
lifted = np.flatnonzero(tcon[:, tslot] == 0)
print(f"  support contact: frames with support {int(tcon[:, tslot].sum())}/{n}; first airborne frame {int(lifted[0]) if len(lifted) else -1}, last airborne frame {int(lifted[-1]) if len(lifted) else -1}")
print(f"  obj-obj contact frames for target: {int(oocon[:, tslot].sum())}; any-slot obj-obj frames: {int((oocon.sum(1) > 0).sum())}")
print(f"  arm (non-gripper) contact frames: {int((armc > 0).sum())}; gripper-static contact frames: {int((gsc > 0).sum())}")
z = pos[:, tslot, 2]
print(f"  target z: start {z[0]:.3f} max {z.max():.3f} (frame {int(z.argmax())}) end {z[-1]:.3f}")
xy_start, xy_end = pos[0, tslot, :2], pos[-1, tslot, :2]
print(f"  target xy: start {np.round(xy_start, 3)} end {np.round(xy_end, 3)}  moved {np.linalg.norm(xy_end - xy_start):.3f} m")
ncon = col("priv.n_contacts").reshape(-1)
print(f"  n_contacts: min {ncon.min():.0f} max {ncon.max():.0f}")
if "priv.obj_grasped_pads" in ds.features:
    gp = col("priv.obj_grasped_pads")[:, tslot]
    lf = col("priv.obj_left_finger_contact")[:, tslot]
    rf = col("priv.obj_right_finger_contact")[:, tslot]
    rest = col("priv.obj_resting")[:, tslot]
    gfix = col("priv.gripper_fixture_contacts").reshape(-1)
    print(f"  schema v2: grasp(fingers) frames {int(grasp[:, tslot].sum())} vs grasp(pads) {int(gp.sum())}; left-finger {int(lf.sum())} right-finger {int(rf.sum())}; resting frames {int(rest.sum())}/{n}; gripper-fixture contact frames {int((gfix > 0).sum())}")
    fq = col("priv.fixture_qpos")
    fvalid = col("priv.fixture_valid")[0]
    names = meta.get("fixture_joint_names", [])
    for j in range(int(fvalid.sum())):
        nm = names[j] if j < len(names) else f"joint{j}"
        print(f"  fixture joint {nm}: start {fq[0, j]:+.3f} min {fq[:, j].min():+.3f} max {fq[:, j].max():+.3f} end {fq[-1, j]:+.3f}")
    print(f"  goal_state: {meta.get('goal_state')}")
eef = col("priv.eef_pos")
print(f"  eef z range: {eef[:, 2].min():.3f} .. {eef[:, 2].max():.3f}")

# sidecar npz
npz = np.load(root / "sidecar" / f"episode_{ep:06d}.npz")
print(f"\nsidecar npz keys: {list(npz.keys())}")
print(f"  sim_states {npz['sim_states'].shape}  chunk_start_frames {npz['chunk_start_frames'][:5]}... init_sim_state {npz['init_sim_state'].shape}")
print(f"sidecar json: source={meta['source']} init_mode={meta['init_mode']} init_state_id={meta['init_state_id']} success={meta['success']} length={meta['length']} n_chunks={meta['n_chunks']}")

# image orientation check: recorded frame vs lerobot/libero demo frame
mid = from_idx + n // 2
item = ds[mid]
img = item["observation.images.image"]
img = (img.permute(1, 2, 0).numpy() * 255).astype(np.uint8) if isinstance(img, torch.Tensor) else np.asarray(img)
wrist = item["observation.images.image2"]
wrist = (wrist.permute(1, 2, 0).numpy() * 255).astype(np.uint8) if isinstance(wrist, torch.Tensor) else np.asarray(wrist)

snap = glob.glob(str(Path.home() / ".cache/huggingface/hub/datasets--lerobot--libero/snapshots/*"))
ref_img = None
if snap:
    ref = LeRobotDataset("lerobot/libero", root=snap[0])
    # find a frame of the same task via the task index (episode table has no task strings in this version)
    ref_idx = 60
    try:
        tidx = int(ref.meta.tasks.loc[meta["task_language"], "task_index"])
        task_col = np.asarray(ref.hf_dataset["task_index"]).reshape(-1)
        hits = np.flatnonzero(task_col == tidx)
        ref_idx = int(hits[0]) + 60 if len(hits) else 60
        print(f"\nreference: lerobot/libero task_index {tidx} '{meta['task_language']}', frame {ref_idx}")
    except Exception as e:  # pragma: no cover
        print(f"\nreference task lookup failed ({e}); using frame {ref_idx}")
    ritem = ref[ref_idx]
    ref_img = ritem["observation.images.image"]
    ref_img = (ref_img.permute(1, 2, 0).numpy() * 255).astype(np.uint8)

WIN_OUT.mkdir(parents=True, exist_ok=True)
tiles = [img, wrist] + ([ref_img] if ref_img is not None else [])
canvas = np.concatenate(tiles, axis=1)
out = WIN_OUT / f"verify_{name}_ep{ep}.png"
Image.fromarray(canvas).save(out)
print(f"wrote {out}  (left: recorded agentview, middle: recorded wrist, right: lerobot/libero demo agentview)")
print("VERIFY_OK")
