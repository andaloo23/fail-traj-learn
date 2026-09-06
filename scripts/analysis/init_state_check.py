"""Audit shifted initial states: at frame 0, is any object touching another object, tipped/raised relative to its
resting pose in the anchor data, or far from the table centre? Prints per-prefix counts.

Usage: init_state_check.py <anchor_prefix> <shifted_prefix> [...]
"""
import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from lerobot.datasets.lerobot_dataset import LeRobotDataset

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))


def datasets(prefix):
    return sorted(Path(p).name for p in glob.glob(str(PROJ / "data" / f"{prefix}__t*")))


def frame0(name):
    root = PROJ / "data" / name
    ds = LeRobotDataset(f"fail_traj/{name}", root=root)
    out = []
    for ep in range(ds.num_episodes):
        f0 = int(ds.meta.episodes["dataset_from_index"][ep])
        row = ds.hf_dataset.select(range(f0, f0 + 1))
        meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
        pos = np.asarray(row["priv.obj_pos"][0]).reshape(-1, 3)
        quat = np.asarray(row["priv.obj_quat"][0]).reshape(-1, 4)
        valid = np.asarray(row["priv.obj_valid"][0]).astype(bool)
        oo = np.asarray(row["priv.obj_obj_contact"][0])
        sup = np.asarray(row["priv.obj_support_contact"][0])
        out.append((meta["object_slots"], pos, quat, valid, oo, sup, meta["task_id"], ep, meta["success"]))
    return out


anchor, shifted = sys.argv[1], sys.argv[2:]
# resting height and "up" axis per (task, object) from the anchor data
rest_z = defaultdict(list)
rest_up = defaultdict(list)
for name in datasets(anchor):
    for slots, pos, quat, valid, oo, sup, tid, ep, succ in frame0(name):
        for s, nm in enumerate(slots):
            if valid[s]:
                x, y, z, w = quat[s]
                up = np.array([2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)])  # world z axis of the body
                rest_z[(tid, nm)].append(pos[s, 2])
                rest_up[(tid, nm)].append(up)
rest_z = {k: float(np.median(v)) for k, v in rest_z.items()}
rest_up = {k: np.median(np.stack(v), axis=0) for k, v in rest_up.items()}

for prefix in shifted:
    n = touching = raised = tipped = far = airborne = flagged = flagged_fail = 0
    examples = []
    for name in datasets(prefix):
        for slots, pos, quat, valid, oo, sup, tid, ep, succ in frame0(name):
            n += 1
            flags = []
            for s, nm in enumerate(slots):
                if not valid[s]:
                    continue
                if nm.startswith("basket"):
                    continue  # objects may legitimately rest inside/against the basket in some layouts
                if oo[s] > 0:
                    flags.append(f"{nm}:touch")
                if sup[s] == 0 and oo[s] == 0:
                    flags.append(f"{nm}:airborne")
                dz = pos[s, 2] - rest_z.get((tid, nm), pos[s, 2])
                if abs(dz) > 0.02:
                    flags.append(f"{nm}:dz={dz:+.3f}")
                x, y, z, w = quat[s]
                up = np.array([2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)])
                ref = rest_up.get((tid, nm))
                # yaw about world z preserves the vertical component of the body axis; compare only that
                if ref is not None and abs(float(up[2]) - float(ref[2])) > 0.34:
                    flags.append(f"{nm}:tipped")
                if np.hypot(pos[s, 0], pos[s, 1]) > 0.55 or pos[s, 2] < -0.05:  # table edge is beyond 0.5 m
                    flags.append(f"{nm}:far")
            touching += any(":touch" in f for f in flags)
            raised += any(":dz=" in f for f in flags)
            tipped += any(":tipped" in f for f in flags)
            far += any(":far" in f for f in flags)
            airborne += any(":airborne" in f for f in flags)
            bad = any((":airborne" in f) or (":far" in f) or (":touch" in f) for f in flags)
            flagged += bad
            flagged_fail += bad and not succ
            if bad and len(examples) < 6:
                examples.append(f"    {name} ep {ep}: {' '.join(flags)}")
    print(f"{prefix}: {n} episodes | contact: {touching} | airborne: {airborne} | dz>2cm: {raised} | tipped: {tipped} | far: {far} || BAD INIT (airborne, far or contact): {flagged} of which failures {flagged_fail}")
    for e in examples:
        print(e)
