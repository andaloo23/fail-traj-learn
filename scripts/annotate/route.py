"""Decide which episodes get the full VLM pass (sim-only routing, uses privileged columns).

  failure                      -> vlm   (reason: failure)
  success with re-grasp        -> vlm   (>= 2 grasp onsets on the target)
  success with a long stall    -> vlm   (>= 40 idle frames = 2 s)
  success with arm collision   -> vlm   (>= 5 arm-contact frames)
  slow success                 -> vlm   (length > 1.5 x median success length of the same task)
  otherwise (clean success)    -> clean (default labels: progress everywhere), except a deterministic 10 %
                                  control sample that also goes to the VLM (false-alarm rate).
On real data (OOPSIE) there is no oracle: route on the human outcome label instead.
"""
import hashlib
from collections import defaultdict

import numpy as np

from common import read_episodes_jsonl


def success_length_medians(names):
    """(suite, task_id) -> median length of successful episodes across the given datasets."""
    by_task = defaultdict(list)
    for n in names:
        for e in read_episodes_jsonl(n):
            if e["success"]:
                by_task[(e["suite"], int(e["task_id"]))].append(int(e["length"]))
    return {k: float(np.median(v)) for k, v in by_task.items()}


def _control_sample(name, ep, frac=0.10):
    h = int(hashlib.md5(f"{name}:{ep}".encode()).hexdigest(), 16)
    return (h % 1000) < int(frac * 1000)


def route_episode(ep, medians, control_frac=0.10):
    """ep: common.Episode. Returns dict(route='vlm'|'clean', reasons=[...], stats={...})."""
    if not ep.success:
        return {"route": "vlm", "reasons": ["failure"], "stats": {}}
    target = ep.col("priv.target_mask")[0]
    t = int(np.flatnonzero(target)[0]) if target.any() else 0
    grasp = ep.col("priv.obj_grasped")[:, t] > 0
    onsets = int(np.sum(grasp[1:] & ~grasp[:-1]) + int(grasp[0]))
    arm = int((ep.col("priv.arm_contacts").reshape(-1) > 0).sum())
    speed = np.linalg.norm(np.diff(ep.eef_xyz, axis=0), axis=1)
    dgrip = np.abs(np.diff(ep.gripper_aperture))
    idle = (speed < 0.002) & (dgrip < 0.002)
    longest, cur = 0, 0
    for v in idle:
        cur = cur + 1 if v else 0
        longest = max(longest, cur)
    med = medians.get((ep.meta["suite"], int(ep.meta["task_id"])), float(ep.n))
    reasons = []
    if onsets >= 2:
        reasons.append("regrasp")
    if longest >= 40:
        reasons.append("stall")
    if arm >= 5:
        reasons.append("collision")
    if ep.n > 1.5 * med:
        reasons.append("slow")
    stats = {"grasp_onsets": onsets, "longest_idle": int(longest), "arm_contact_frames": arm, "len": ep.n, "task_median_success_len": med}
    if reasons:
        return {"route": "vlm", "reasons": reasons, "stats": stats}
    if _control_sample(ep.name, ep.ep, control_frac):
        return {"route": "vlm", "reasons": ["control"], "stats": stats}
    return {"route": "clean", "reasons": ["clean_success"], "stats": stats}


def default_clean_record(ep):
    """Annotation-shaped record for a clean success without a VLM call."""
    n = ep.n_chunks
    return {
        "k": 0, "outcome": "success", "outcome_agreement": 1.0, "cause": "unclear", "cause_votes": {}, "cause_agreement": 1.0,
        "failure_symptom": None, "root_cause": None,
        "landmarks": {k: {"value": None, "n_votes": 0, "spread": None} for k in ("failure_onset", "decisive_error", "visible_failure", "recoverable_until")},
        "chunk_label": ["progress"] * n, "chunk_q": [0.0] * n, "chunk_self_confidence": [0.0] * n, "chunk_cause": [None] * n,
        "segments": [{"start": 0, "end": n - 1, "label": "progress", "confidence": 0.0}], "mean_q": 0.0,
        "q_kind": "unverified_default",
        "sample_agreement": [], "medoid_sample": None,
    }
