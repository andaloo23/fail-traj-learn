"""Count failed episodes whose target object ends geometrically inside the goal container although LIBERO's
`In` predicate said no.

LIBERO's SiteObject.in_box computes the region's half-extents as abs(R @ size) where R is the container's rotation,
so a container yawed near 45 degrees gets a contain region that collapses in x/y. Our shifted-init mode yaws every
movable object, including baskets, so part of the shifted-init "failures" are predicate artifacts. This tool applies a
rotation-correct box test (object position expressed in the container's frame) to the last frame of every episode.

Usage: predicate_artifacts.py <dataset_prefix_or_name> [...]    (prefix expands to <prefix>__t*)
"""
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np

from lerobot.datasets.lerobot_dataset import LeRobotDataset

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))
# basket contain_region from stable_scanned_objects/basket/basket.xml: box half-size and offset in the basket frame
REGIONS = {"basket": (np.array([0.0, 0.0, 0.07185]), np.array([0.06108, 0.06108, 0.06949]))}


def quat_xyzw_to_mat(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def libero_in_box(cpos, cmat, off, size, opos):
    """LIBERO's actual test (site_object.py), including the abs(R @ size) hack and the 1 cm lower slack."""
    spos = cpos + cmat @ off
    total = np.abs(cmat @ size)
    lb, ub = spos - total, spos + total
    lb[2] -= 0.01
    return bool(np.all(opos > lb) and np.all(opos < ub))


def correct_in_box(cpos, cmat, off, size, opos):
    local = cmat.T @ (opos - cpos) - off
    lb = -size.copy()
    lb[2] -= 0.01
    return bool(np.all(local > lb) and np.all(local < size))


names = []
for a in sys.argv[1:]:
    hits = sorted(glob.glob(str(PROJ / "data" / f"{a}__t*")))
    names += [Path(h).name for h in hits] if hits else [a]

tot = {"fail": 0, "inside_correct": 0, "inside_libero": 0, "yaw45_container": 0, "excluded": 0}
EXCL_PATH = Path(__file__).resolve().parent / "exclusions.json"
EXCL = {}
if EXCL_PATH.exists():
    EXCL = {k: {e["episode_index"] for e in v} for k, v in json.load(open(EXCL_PATH)).items() if not k.startswith("_")}
for name in names:
    root = PROJ / "data" / name
    ds = LeRobotDataset(f"fail_traj/{name}", root=root)
    for ep in range(ds.num_episodes):
        meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
        goal = meta.get("goal_state") or []
        # find (target object, container) pairs from `in` goals
        pairs = []
        for g in goal:
            if len(g) == 3 and g[0].lower() == "in":
                obj, region = g[1], g[2]
                for kind in REGIONS:
                    if kind in region:
                        owner = region.split("_contain_region")[0]
                        pairs.append((obj, owner, kind))
        if not pairs:  # schema v1 sidecars have no goal_state; libero_object targets are [object, basket]
            tg = meta.get("target_objects") or []
            for kind in REGIONS:
                owners = [t for t in tg if kind in t]
                objs = [t for t in tg if kind not in t]
                if owners and objs:
                    pairs.append((objs[0], owners[0], kind))
        if not pairs:
            continue
        if ep in EXCL.get(name, ()):
            tot["excluded"] += 1
            continue
        f1 = int(ds.meta.episodes["dataset_to_index"][ep])
        # Only failures are judged: the last frame of a successful episode is the pre-step state of the frame in which
        # the predicate fired, so the object is typically still just outside the region there.
        row = ds.hf_dataset.select(range(f1 - 1, f1))
        pos = np.asarray(row["priv.obj_pos"][0]).reshape(-1, 3)
        quat = np.asarray(row["priv.obj_quat"][0]).reshape(-1, 4)
        slots = meta["object_slots"]
        for obj, owner, kind in pairs:
            if obj not in slots or owner not in slots:
                continue
            o, c = slots.index(obj), slots.index(owner)
            cmat = quat_xyzw_to_mat(quat[c].astype(np.float64))
            off, size = REGIONS[kind]
            yaw = np.degrees(np.arctan2(cmat[1, 0], cmat[0, 0]))
            corr = correct_in_box(pos[c], cmat, off, size, pos[o])
            lib = libero_in_box(pos[c], cmat, off, size, pos[o])
            eff = np.abs(cmat @ size)
            if not meta["success"]:
                tot["fail"] += 1
                tot["inside_correct"] += int(corr)
                tot["inside_libero"] += int(lib)
                tot["yaw45_container"] += int(min(eff[0], eff[1]) < 0.03)
                if corr or lib:
                    print(f"{name} ep {ep}: FAIL but {obj} inside {owner} (correct={corr} libero={lib}) | container yaw {yaw:+.0f} deg, effective half-size xy {eff[0]:.3f},{eff[1]:.3f} | obj z {pos[o][2]:.3f}")
print(f"\nfailed episodes with an `in` goal: {tot['fail']}; ending inside the container by the rotation-correct test: {tot['inside_correct']}; "
      f"by LIBERO's own test: {tot['inside_libero']}; container yawed so that LIBERO's region collapsed (<3 cm half-size): {tot['yaw45_container']}; excluded by exclusions.json: {tot['excluded']}")
