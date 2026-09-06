"""Per-object summary of one episode: where each object started and ended, how far it moved, and for how many
frames it was gripper-contacted / grasped / airborne. Answers "did the policy pick up the wrong thing?".

Usage: episode_objects.py <dataset_name> <episode_index>
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

from lerobot.datasets.lerobot_dataset import LeRobotDataset

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))
name, ep = sys.argv[1], int(sys.argv[2])
root = PROJ / "data" / name
ds = LeRobotDataset(f"fail_traj/{name}", root=root)
meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
slots = meta["object_slots"]
f0 = int(ds.meta.episodes["dataset_from_index"][ep])
f1 = int(ds.meta.episodes["dataset_to_index"][ep])
n = f1 - f0
rows = ds.hf_dataset.select(range(f0, f1))
col = lambda k: np.stack([np.asarray(x) for x in rows[k]])  # noqa: E731
pos = col("priv.obj_pos").reshape(n, -1, 3)
gcon = col("priv.obj_gripper_contact")
grasp = col("priv.obj_grasped")
sup = col("priv.obj_support_contact")
oo = col("priv.obj_obj_contact")
eef = col("priv.eef_pos")
grip = col("observation.state")[:, 6]
print(f"{name} ep {ep}: '{meta['task_language']}' success={meta['success']} len={n} targets={meta['target_objects']} goal={meta.get('goal_state')}")
closed = grip < 0.02
runs = []
i = 0
while i < n:
    if closed[i]:
        j = i
        while j < n and closed[j]:
            j += 1
        runs.append((i, j - 1))
        i = j
    else:
        i += 1
print(f"gripper closed intervals (frames): {runs}")
print(f"eef z min {eef[:, 2].min():.3f} at frame {int(eef[:, 2].argmin())}; eef xy at that frame {np.round(eef[eef[:, 2].argmin(), :2], 3)}")
print(f"\n{'object':20s} {'start xyz':>24s} {'end xyz':>24s} {'moved':>6s} {'grip_c':>6s} {'grasp':>6s} {'air':>5s} {'zmax':>6s}")
for s, nm in enumerate(slots):
    d = float(np.linalg.norm(pos[-1, s] - pos[0, s]))
    flag = "*" if nm in meta["target_objects"] else " "
    air = int(((sup[:, s] == 0) & (oo[:, s] == 0)).sum())
    print(f"{flag}{nm:19s} {np.round(pos[0, s], 3)!s:>24s} {np.round(pos[-1, s], 3)!s:>24s} {d:6.3f} {int(gcon[:, s].sum()):6d} {int(grasp[:, s].sum()):6d} {air:5d} {pos[:, s, 2].max():6.3f}")
touched = [slots[s] for s in range(len(slots)) if gcon[:, s].any()]
print(f"\nobjects touched by the gripper: {touched or 'none'}")
for s in range(len(slots)):
    if gcon[:, s].any():
        fr = np.flatnonzero(gcon[:, s])
        print(f"  {slots[s]}: contact frames {fr[0]}..{fr[-1]} ({len(fr)} frames), grasp frames {int(grasp[:, s].sum())}, z range {pos[fr, s, 2].min():.3f}..{pos[fr, s, 2].max():.3f}")
