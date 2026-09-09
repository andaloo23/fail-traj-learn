"""Audit initial states (frame 0) of recorded datasets: is any object touching another object, airborne (no support
and no object contact), tipped, raised, or far from where that object normally starts in that task?

References are built per (suite, task, object) from the median frame-0 pose over ALL audited datasets, so every
suite is judged against its own scenes (a libero_10 kitchen table is not the libero_object living-room table). Passing
an anchor prefix first (standard-init data) just adds to the reference pool. Bad init = airborne, far, or contact.

Usage: init_state_check.py <prefix> [prefix ...]
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
FAR_M = 0.30      # xy distance from the object's median start in that task; any shift level we use is <= 0.16 m
DZ_M = 0.02       # raised/sunk relative to the median start height
TIP_COS = 0.34    # change of the body's up-axis z component


def datasets(prefix):
    return sorted(Path(p).name for p in glob.glob(str(PROJ / "data" / f"{prefix}__t*")))


def up_axis(q):
    x, y, z, w = q
    return np.array([2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)])


def frame0(name):
    root = PROJ / "data" / name
    ds = LeRobotDataset(f"fail_traj/{name}", root=root)
    out = []
    for ep in range(ds.num_episodes):
        f0 = int(ds.meta.episodes["dataset_from_index"][ep])
        f1 = int(ds.meta.episodes["dataset_to_index"][ep])
        rows3 = ds.hf_dataset.select(range(f0, min(f0 + 3, f1)))
        row = rows3.select(range(0, 1))
        meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
        pos = np.asarray(row["priv.obj_pos"][0]).reshape(-1, 3)
        quat = np.asarray(row["priv.obj_quat"][0]).reshape(-1, 4)
        valid = np.asarray(row["priv.obj_valid"][0]).astype(bool)
        oo = np.asarray(row["priv.obj_obj_contact"][0])
        sup = np.asarray(row["priv.obj_support_contact"][0])
        # airborne only if unsupported for the first three frames (a 1 mm settle at frame 0 is not a bad init)
        sup3 = np.stack([np.asarray(x) for x in rows3["priv.obj_support_contact"]]).max(axis=0)
        oo3 = np.stack([np.asarray(x) for x in rows3["priv.obj_obj_contact"]]).max(axis=0)
        sup = np.maximum(sup, np.minimum(1, sup3 + oo3))
        out.append((meta["object_slots"], pos, quat, valid, oo, sup, (meta["suite"], meta["task_id"]), ep, meta["success"]))
    return out


prefixes = sys.argv[1:]
EXCL_PATH = Path(__file__).resolve().parent / "exclusions.json"
EXCL = {}
if EXCL_PATH.exists():
    EXCL = {k: {e["episode_index"] for e in v} for k, v in json.load(open(EXCL_PATH)).items() if not k.startswith("_")}
data = {p: [r for name in datasets(p) for r in [(name, x) for x in frame0(name)]] for p in prefixes}

# reference start pose per (suite, task, object): median over everything audited
ref_xy, ref_z, ref_up = defaultdict(list), defaultdict(list), defaultdict(list)
for rows in data.values():
    for _, (slots, pos, quat, valid, oo, sup, key, ep, succ) in rows:
        for s, nm in enumerate(slots):
            if valid[s]:
                ref_xy[key + (nm,)].append(pos[s, :2])
                ref_z[key + (nm,)].append(pos[s, 2])
                ref_up[key + (nm,)].append(up_axis(quat[s]))
ref_xy = {k: np.median(np.stack(v), axis=0) for k, v in ref_xy.items()}
ref_z = {k: float(np.median(v)) for k, v in ref_z.items()}
ref_up = {k: np.median(np.stack(v), axis=0) for k, v in ref_up.items()}

for prefix, rows in data.items():
    n = touching = raised = tipped = far = airborne = flagged = flagged_fail = excluded = 0
    examples = []
    for name, (slots, pos, quat, valid, oo, sup, key, ep, succ) in rows:
        n += 1
        if ep in EXCL.get(name, ()):
            excluded += 1
            continue
        flags = []
        for s, nm in enumerate(slots):
            if not valid[s]:
                continue
            if nm.startswith("basket"):
                continue  # objects may legitimately rest inside/against the basket in some layouts
            r = key + (nm,)
            if oo[s] > 0:
                flags.append(f"{nm}:touch")
            if sup[s] == 0 and oo[s] == 0:
                flags.append(f"{nm}:airborne")
            dz = pos[s, 2] - ref_z[r]
            if abs(dz) > DZ_M:
                flags.append(f"{nm}:dz={dz:+.3f}")
            if abs(float(up_axis(quat[s])[2]) - float(ref_up[r][2])) > TIP_COS:
                flags.append(f"{nm}:tipped")
            dxy = float(np.linalg.norm(pos[s, :2] - ref_xy[r]))
            if dxy > FAR_M or pos[s, 2] < ref_z[r] - 0.05:
                flags.append(f"{nm}:far={dxy:.2f}")
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
    print(f"{prefix}: {n} episodes | contact: {touching} | airborne: {airborne} | dz>2cm: {raised} | tipped: {tipped} | far: {far} || BAD INIT (airborne, far or contact): {flagged} of which failures {flagged_fail} | excluded by exclusions.json: {excluded}")
    for e in examples:
        print(e)
