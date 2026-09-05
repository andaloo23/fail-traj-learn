"""Per-episode progress / informativeness analysis from privileged columns.

For each episode, detects the pick-and-place stage reached and how much of the episode was spent stalled,
then reports a distribution per dataset group. Stages (target object = first obj_of_interest):
  0 none      : never touched the target (nor any fixture)
  1 reached   : gripper touched the target (or a fixture, for articulated tasks)
  2 grasped   : both-pad grasp OR (gripper contact AND target airborne)   [robust to the pad-only rule]
  3 lifted    : target airborne while grasped
  4 transported: target moved >= 15 cm in xy from its start while held, or came within 12 cm of the goal object
  5 placed    : success predicate fired
progress p = stage/5 (continuous credit inside stage 3->4 by transport fraction).
stall_frac  = fraction of frames in the trailing window after the last stage change where the end-effector
              moves < 2 mm/frame and the gripper aperture is not changing.
usefulness u in [-1, 1] (diagnostic only, NOT a training reward):
  success: u = 1 - 0.4 * (len / max_len)          -> fast success ~0.8..1.0, slow success ~0.6
  failure: u = -1 + 1.6 * p * (1 - 0.5 * stall_frac) -> stall-from-start = -1, late failure ~ +0.3..0.6

Usage: episode_progress.py [name_or_prefix ...]   (default: all datasets)   add --episodes to list every episode
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from lerobot.datasets.lerobot_dataset import LeRobotDataset

DATA = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn")) / "data"
LIST_EPISODES = "--episodes" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
all_names = sorted(p.name for p in DATA.iterdir() if (p / "meta" / "info.json").exists() and (p / "episodes.jsonl").exists())
names = [n for n in all_names if not args or any(n == a or n.startswith(a + "__t") for a in args)]

STAGE_NAMES = ["none", "reached", "grasped", "lifted", "transported", "placed"]


def analyze_episode(ds, ep, meta):
    f0 = int(ds.meta.episodes["dataset_from_index"][ep])
    f1 = int(ds.meta.episodes["dataset_to_index"][ep])
    n = f1 - f0
    rows = ds.hf_dataset.select(range(f0, f1))
    col = lambda k: np.stack([np.asarray(x) for x in rows[k]])  # noqa: E731
    target_mask = col("priv.target_mask")[0]
    tslots = np.flatnonzero(target_mask)
    t = int(tslots[0]) if len(tslots) else 0
    goal = int(tslots[1]) if len(tslots) > 1 else None
    pos = col("priv.obj_pos").reshape(n, -1, 3)
    gcon = col("priv.obj_gripper_contact")[:, t]
    grasp = col("priv.obj_grasped")[:, t]
    sup = col("priv.obj_support_contact")[:, t]
    oo = col("priv.obj_obj_contact")[:, t]
    gstat = col("priv.gripper_static_contacts").reshape(-1)
    eef = col("priv.eef_pos")
    grip = col("observation.state")[:, 6]
    succ = col("next.success").reshape(-1)

    airborne = (sup == 0) & (oo == 0)
    held = (grasp > 0) | ((gcon > 0) & airborne)
    reached_f = int(np.argmax(gcon > 0)) if (gcon > 0).any() else (int(np.argmax(gstat > 0)) if (gstat > 0).any() else -1)
    grasped_f = int(np.argmax(held)) if held.any() else -1
    lifted_f = int(np.argmax(held & airborne)) if (held & airborne).any() else -1
    # transport: xy displacement of target while held, or approach to goal object
    xy0 = pos[0, t, :2]
    disp = np.linalg.norm(pos[:, t, :2] - xy0, axis=1)
    if goal is not None:
        d_goal = np.linalg.norm(pos[:, t, :2] - pos[:, goal, :2], axis=1)
        d_goal0 = float(d_goal[0])
        transport_frac = float(np.clip(1 - d_goal.min() / max(d_goal0, 1e-6), 0, 1)) if d_goal0 > 0.12 else 1.0
        transported = (d_goal <= 0.12) & (disp > 0.05)
    else:
        transport_frac = float(np.clip(disp.max() / 0.15, 0, 1))
        transported = disp >= 0.15
    transported_f = int(np.argmax(transported)) if transported.any() else -1
    placed_f = int(np.argmax(succ)) if succ.any() else -1

    stage = 0
    stage_frames = [0, reached_f, grasped_f, lifted_f, transported_f, placed_f]
    for s in range(1, 6):
        if stage_frames[s] >= 0:
            stage = s
    p = stage / 5.0
    if stage == 3:
        p = (3 + transport_frac) / 5.0

    # stall: trailing window after last stage change
    last_change = max([f for f in stage_frames if f >= 0] + [0])
    speed = np.linalg.norm(np.diff(eef, axis=0), axis=1)
    dgrip = np.abs(np.diff(grip))
    idle = (speed < 0.002) & (dgrip < 0.002)
    tail = idle[last_change:] if last_change < len(idle) else idle[-1:]
    stall_frac = float(tail.mean()) if len(tail) else 0.0
    # also: longest idle run anywhere
    runs, cur = [], 0
    for v in idle:
        cur = cur + 1 if v else 0
        runs.append(cur)
    longest_idle = int(max(runs)) if runs else 0

    success = bool(meta["success"])
    max_len = int(meta.get("max_steps", n))
    if success:
        u = 1.0 - 0.4 * (n / max_len)
    else:
        u = -1.0 + 1.6 * p * (1.0 - 0.5 * stall_frac)
    return {
        "episode": ep, "success": success, "len": n, "stage": stage, "stage_name": STAGE_NAMES[stage], "p": round(p, 2),
        "reached_f": reached_f, "grasped_f": grasped_f, "lifted_f": lifted_f, "transported_f": transported_f,
        "stall_frac": round(stall_frac, 2), "longest_idle": longest_idle, "u": round(float(u), 2),
        "task": meta["task_language"], "suite": meta["suite"], "task_id": meta["task_id"],
    }


groups = defaultdict(list)
for name in names:
    root = DATA / name
    try:
        ds = LeRobotDataset(f"fail_traj/{name}", root=root)
    except Exception as e:
        print(f"{name}: cannot load ({str(e)[:80]})")
        continue
    for ep in range(ds.num_episodes):
        meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
        r = analyze_episode(ds, ep, meta)
        r["dataset"] = name
        groups[name.split("__t")[0]].append(r)

for g, rs in groups.items():
    n = len(rs)
    fails = [r for r in rs if not r["success"]]
    print(f"\n=== {g}: {n} episodes, success {n - len(fails)}/{n} ===")
    hist = defaultdict(int)
    for r in fails:
        hist[r["stage_name"]] += 1
    print("  failure stage reached: " + ", ".join(f"{s}={hist[s]}" for s in STAGE_NAMES if hist[s]) if fails else "  no failures")
    if fails:
        p = np.array([r["p"] for r in fails]); st = np.array([r["stall_frac"] for r in fails]); u = np.array([r["u"] for r in fails])
        print(f"  failures: mean progress {p.mean():.2f}, share with p>=0.4 (grasp or beyond) {100 * (p >= 0.4).mean():.0f}%, "
              f"mean stall_frac {st.mean():.2f}, usefulness mean {u.mean():.2f} (min {u.min():.2f}, max {u.max():.2f})")
    us = np.array([r["u"] for r in rs])
    print(f"  all episodes: usefulness mean {us.mean():.2f}; distribution u<-0.5: {int((us < -0.5).sum())}, -0.5..0: {int(((us >= -0.5) & (us < 0)).sum())}, 0..0.5: {int(((us >= 0) & (us < 0.5)).sum())}, >=0.5: {int((us >= 0.5).sum())}")
    if LIST_EPISODES:
        for r in sorted(rs, key=lambda r: (r["dataset"], r["episode"])):
            print(f"    {r['dataset']:32s} ep{r['episode']:3d} ok={int(r['success'])} len={r['len']:3d} stage={r['stage_name']:11s} p={r['p']:.2f} stall={r['stall_frac']:.2f} idle_max={r['longest_idle']:3d} u={r['u']:+.2f}")
