"""Print end-of-episode geometry for diagnosing 'looks placed but no success' cases.

Usage: episode_end_state.py <dataset_name> <episode_index> [n_last_frames]
"""
import json
import sys
from pathlib import Path

import numpy as np

from lerobot.datasets.lerobot_dataset import LeRobotDataset

PROJ = Path("/home/aliu/projects/fail-traj-learn")
name, ep = sys.argv[1], int(sys.argv[2])
n_last = int(sys.argv[3]) if len(sys.argv) > 3 else 3
root = PROJ / "data" / name
ds = LeRobotDataset(f"fail_traj/{name}", root=root)
meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
slots = meta["object_slots"]
f0 = int(ds.meta.episodes["dataset_from_index"][ep])
f1 = int(ds.meta.episodes["dataset_to_index"][ep])
rows = ds.hf_dataset.select(range(f1 - n_last, f1))
col = lambda k: np.stack([np.asarray(x) for x in rows[k]])  # noqa: E731
pos = col("priv.obj_pos").reshape(n_last, -1, 3)
quat = col("priv.obj_quat").reshape(n_last, -1, 4)
gcon = col("priv.obj_gripper_contact")
grasp = col("priv.obj_grasped")
sup = col("priv.obj_support_contact")
oo = col("priv.obj_obj_contact")
eef = col("priv.eef_pos")
grip = col("observation.state")[:, 6:8]
succ = col("next.success").reshape(-1)
print(f"{name} ep {ep}: task='{meta['task_language']}' success={meta['success']} len={meta['length']} targets={meta['target_objects']}")
for i in range(n_last):
    fr = f1 - n_last + i - f0
    print(f"\n-- frame {fr} success={bool(succ[i])} eef={np.round(eef[i], 3)} gripper_qpos={np.round(grip[i], 3)}")
    for s, nm in enumerate(slots):
        flag = "*" if nm in meta["target_objects"] else " "
        print(f"  {flag}{nm:18s} pos={np.round(pos[i, s], 3)} quat(xyzw)={np.round(quat[i, s], 2)} grip_c={int(gcon[i, s])} grasp={int(grasp[i, s])} support={int(sup[i, s])} obj_obj={int(oo[i, s])}")
