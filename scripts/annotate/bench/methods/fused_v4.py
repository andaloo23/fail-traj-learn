"""fused_v4: the gripper COMMAND as the skeleton of the held state, the VLM as a verifier on three frames per candidate
segment, the aperture as the tie-breaker; events from the fused segments; wrist close-up identification of the held
object; event_first_v2.complete for chunk labels, decisive chunk and cause. No chunk VLM passes.

Motivation (measured on the dev set): the visual per-frame held/empty scan at stride 5 is wrong on up to 76 % of
frames (flat boxes read as empty, the gripper housing read as held) and aperture+command alone gives correct events on
only 35 % of episodes (wide cartons sit at 3.4-4.0 cm near the open limit, closed-on-nothing at 0.3-0.5 cm overlaps
thin objects, pushes with closed fingers count as held in the reference). The command is reliable about WHEN the
robot tries to hold; the VLM decides WHETHER something is held in each attempt, on a few well-chosen frames.

Protocol
  1. candidates: maximal runs of command CLOSE (cmd > 0) of >= close_min_run frames, trimmed by trim_start frames at
     the start (fingers travelling). Inside a run a split point is the onset of an aperture collapse below
     split_collapse_to_m lasting >= split_stay_frames, after the current segment has lasted >= split_min_pre_frames
     and reached >= split_from_m (object lost while still squeezing): [start, split) and [split, end] become
     separate candidates.
  2. verification: for up to max_judged candidates (the longest; the rest stay uncertain) the segmentation_lab
     single-frame held/empty question (both cameras, 2x, greedy) on start+4, middle, end-2 (deduped, clamped), all
     frames of the episode in ONE backend.generate_many call. Segment state = held / empty when >= vote_min of the
     judged frames agree, else the telemetry fallback: held iff the median aperture over the segment is in
     [fallback_held_lo_m, fallback_held_hi_m].
  3. events: per held segment a grasp at (start-1, start); a release at (end, end+1) when the command opens after
     the segment, a drop at (split-1, split) when it ends at a telemetry split, nothing when it reaches the last
     frame. Adjacent held segments separated by < merge_gap_frames frames are merged first.
  4. held_object: lib.identify_held_object on up to identify.max_frames frames from the middle half of the held
     segments; event_first_v2.complete(passes=[]) for labels / decisive / cause.
Every VLM response is cached under workdir keyed by the input hash (a rerun is free). result.json holds the
candidates, per-frame judgments, fused segments and events. Inputs: action[6], observation.state[6], eef position,
cameras; no priv.* column is read.
"""
import copy
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import _event_first_lib as lib  # noqa: E402
import event_first_v2 as v2  # noqa: E402
from common import dump_json  # noqa: E402

STATES = ("held", "empty", "uncertain")

CONFIG = {
    "family": "fused_cmd_vlm",
    "candidates": {
        "close_min_run": 8,            # frames of command CLOSE (cmd > 0) that make a candidate run
        "trim_start": 4,               # frames dropped at the start of every run (fingers travelling)
        "split_collapse_to_m": 0.003,  # aperture below this ...
        "split_stay_frames": 6,        # ... for at least this many frames is a collapse (object lost while squeezing)
        "split_from_m": 0.006,         # the segment before the collapse must have reached this aperture ...
        "split_min_pre_frames": 6,     # ... and lasted this long (a close-on-nothing collapsing early is NOT a split)
        "max_judged": 6,               # candidates verified by the VLM per episode (the longest); the rest are uncertain
    },
    "verify": {
        "kind": "verify", "camera": "both", "scale": 2.0, "temperature": 0.0, "max_new_tokens": 400,
        "frames": "start+4, middle, end-2 (deduped, clamped to the segment)",
        "prompt": "segmentation_lab.STATE_SYSTEM via content_for, one frame per prompt, all frames in one generate_many call",
        "vote_min": 2,                 # judged frames that must agree for a VLM decision (2 of 3)
        "fallback_held_lo_m": 0.006, "fallback_held_hi_m": 0.039,  # telemetry fallback: median aperture in [lo, hi] -> held
        "held_obs_judged_frames": "vlm",  # "vlm": judged frames carry the VLM verdict in held_obs; "segment": the fused decision
    },
    "events": {
        "merge_gap_frames": 4,         # adjacent held segments separated by fewer frames are one hold
        "grasp": "(start-1, start)", "release": "(end, end+1) when the command opens after the segment",
        "drop": "(split-1, split) when the segment ends at a telemetry split", "episode_end": "no event",
        "chunk": "ep.chunk_of_frame(last_before)",
    },
    "identify": {**copy.deepcopy(v2.CONFIG["identify"]), "frames": "middle half of every held segment, spread by lib.pick_frames"},
    "chunk_passes": [], "run_chunk_passes": False,
    "completion": copy.deepcopy(v2.CONFIG["completion"]),
    "batch": v2.CONFIG.get("batch", 8),
    "inputs": "action[6] (gripper command), observation.state[6] (finger coordinate), eef position, cameras; no priv.*",
}


# ----------------------------------------------------------------------------------------------------------------
# 1. candidates from the command and the aperture
# ----------------------------------------------------------------------------------------------------------------
def close_runs(cmd, min_run):
    """Maximal runs [(start, end_inclusive)] of command CLOSE lasting >= min_run frames."""
    return [(int(a), int(b)) for a, b in v2.runs_of(np.asarray(cmd, dtype=float) > 0) if b - a + 1 >= min_run]


def split_points(ap, start, end, ccfg):
    """Onsets of aperture collapses inside [start, end] (a trimmed CLOSE run) that split it into held / closed-empty.

    A split at s needs: ap < split_collapse_to_m from s on for >= split_stay_frames frames (inside the run), the
    current segment [seg_start, s) to be >= split_min_pre_frames long and to have reached >= split_from_m.
    """
    ap = np.asarray(ap, dtype=float)
    to_m, stay = float(ccfg["split_collapse_to_m"]), int(ccfg["split_stay_frames"])
    from_m, min_pre = float(ccfg["split_from_m"]), int(ccfg["split_min_pre_frames"])
    splits, seg_start = [], start
    for a, b in v2.runs_of(ap[start:end + 1] < to_m):
        s = start + a
        if b - a + 1 < stay or s - seg_start < min_pre:
            continue
        pre = ap[seg_start:s]
        if pre.size == 0 or float(pre.max()) < from_m:
            continue
        splits.append(int(s))
        seg_start = s
    return splits


def candidate_segments(ap, cmd, ccfg):
    """Candidate held / closed-empty segments (frames inclusive) from the command runs and the aperture splits."""
    ap = np.asarray(ap, dtype=float)
    n = len(ap)
    trim = int(ccfg["trim_start"])
    out = []
    for a, b in close_runs(cmd, int(ccfg["close_min_run"])):
        start = a + trim
        if start > b:
            continue
        bounds = [start] + split_points(ap, start, b, ccfg) + [b + 1]
        for i in range(len(bounds) - 1):
            s, e = bounds[i], bounds[i + 1] - 1
            last = i == len(bounds) - 2
            reason = "split" if not last else ("episode_end" if b >= n - 1 else "open")
            out.append({"index": len(out), "start": int(s), "end": int(e), "n_frames": int(e - s + 1), "run": [a, b], "part": i,
                        "end_reason": reason, "median_aperture_m": round(float(np.median(ap[s:e + 1])), 5)})
    return out


def judge_frames(seg, offset_start=4, offset_end=2):
    """start+4, middle, end-2, deduped and clamped to the segment."""
    s, e = int(seg["start"]), int(seg["end"])
    return sorted({min(e, s + offset_start), (s + e) // 2, max(s, e - offset_end)})


def select_judged(segments, max_judged):
    """Mark the longest max_judged segments (ties: earliest first) for VLM verification; returns them in frame order."""
    ranked = sorted(segments, key=lambda s: (-s["n_frames"], s["start"]))
    keep = {s["index"] for s in ranked[:int(max_judged)]}
    for seg in segments:
        seg["judged"] = seg["index"] in keep
        seg["judge_frames"] = judge_frames(seg) if seg["judged"] else []
    return [s for s in segments if s["judged"]]


# ----------------------------------------------------------------------------------------------------------------
# 2. verification and fusion
# ----------------------------------------------------------------------------------------------------------------
def judgment_from_row(row):
    """Per-frame verdict from a run_state_queries row: the parsed state, or uncertain when the answer was malformed."""
    parsed = row.get("parsed") or {}
    states = parsed.get("states") or []
    if states and states[0].get("state") in STATES:
        return {"state": str(states[0]["state"]), "object": states[0].get("object")}
    return {"state": "uncertain", "object": None, "error": row.get("error", "no parsed state")}


def fuse_segment(seg, judgments, ap, vcfg):
    """Segment state from the vote over its judged frames, else from the median aperture (in place; returns seg)."""
    votes = Counter(judgments[f]["state"] for f in seg["judge_frames"] if f in judgments)
    seg["votes"] = {s: int(votes.get(s, 0)) for s in STATES}
    vote_min = int(vcfg["vote_min"])
    if not seg.get("judged"):
        seg["state"], seg["decided_by"] = "uncertain", "over_budget"
    elif votes.get("held", 0) >= vote_min:
        seg["state"], seg["decided_by"] = "held", "vote"
    elif votes.get("empty", 0) >= vote_min:
        seg["state"], seg["decided_by"] = "empty", "vote"
    else:
        med = float(np.median(np.asarray(ap, dtype=float)[seg["start"]:seg["end"] + 1]))
        held = float(vcfg["fallback_held_lo_m"]) <= med <= float(vcfg["fallback_held_hi_m"])
        seg["state"], seg["decided_by"] = ("held" if held else "empty"), "telemetry"
    return seg


def frame_states(n, segments, judgments, judged_mode="vlm"):
    """Per-frame state for held_obs: empty outside candidates, the fused decision inside, the VLM verdict on judged frames."""
    states = ["empty"] * int(n)
    for seg in segments:
        for f in range(seg["start"], seg["end"] + 1):
            states[f] = seg["state"]
    if judged_mode == "vlm":
        for f, j in judgments.items():
            states[int(f)] = j["state"] if j["state"] in STATES else "uncertain"
    return states


# ----------------------------------------------------------------------------------------------------------------
# 3. held segments and events
# ----------------------------------------------------------------------------------------------------------------
def merge_held_segments(segments, gap):
    """Held segments in frame order, merging neighbours separated by fewer than `gap` frames (end reason of the last)."""
    merged = []
    for seg in sorted((s for s in segments if s.get("state") == "held"), key=lambda s: s["start"]):
        if merged and seg["start"] - merged[-1]["end"] - 1 < int(gap):
            merged[-1].update({"end": int(seg["end"]), "end_reason": seg["end_reason"]})
            merged[-1]["members"].append(seg["index"])
        else:
            merged.append({"start": int(seg["start"]), "end": int(seg["end"]), "end_reason": seg["end_reason"], "members": [seg["index"]]})
    for h in merged:
        h["n_frames"] = h["end"] - h["start"] + 1
    return merged


def events_from_held_segments(ep, held_segments, held_object=None):
    events = []

    def add(kind, last_before, first_after):
        events.append({"type": kind, "object": held_object, "last_before": int(last_before), "first_after": int(first_after),
                       "chunk": int(ep.chunk_of_frame(int(last_before)))})

    for h in held_segments:
        if h["start"] > 0:
            add("grasp", h["start"] - 1, h["start"])
        if h["end_reason"] == "open":
            add("release", h["end"], h["end"] + 1)
        elif h["end_reason"] == "split":
            add("drop", h["end"], h["end"] + 1)
    return events


def identify_frames(held_segments):
    """The middle half of every held segment (lib.identify_held_object spreads max_frames over them)."""
    frames = set()
    for h in held_segments:
        quarter = h["n_frames"] // 4
        frames.update(range(h["start"] + quarter, h["end"] - quarter + 1))
    return sorted(frames)


# ----------------------------------------------------------------------------------------------------------------
# the adapter
# ----------------------------------------------------------------------------------------------------------------
def run(ep, backend, workdir, cfg=CONFIG):
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    log = lib.CallLog()
    t0 = time.time()
    ccfg, vcfg, ecfg, idc = cfg["candidates"], cfg["verify"], cfg["events"], cfg["identify"]
    ap = np.asarray(ep.gripper_aperture, dtype=float)
    cmd = np.asarray(ep.gripper_cmd, dtype=float)
    n = int(ep.n)

    segments = candidate_segments(ap, cmd, ccfg)
    judged = select_judged(segments, ccfg["max_judged"])
    frames = sorted({f for s in judged for f in s["judge_frames"]})
    rows = []
    if frames:
        rows = lib.run_state_queries(ep, backend, workdir, vcfg["kind"], frames, scale=vcfg["scale"], camera=vcfg["camera"],
                                     temperature=vcfg["temperature"], repeat=0, batched=True, batch=int(cfg.get("batch", 8)), log=log,
                                     max_new_tokens=int(vcfg.get("max_new_tokens", lib.STATE_MAX_NEW_TOKENS)))
    judgments = {int(f): judgment_from_row(r) for f, r in zip(frames, rows)}
    for seg in segments:
        fuse_segment(seg, judgments, ap, vcfg)
    held_segments = merge_held_segments(segments, ecfg["merge_gap_frames"])

    held_object, idents = None, []
    id_frames = identify_frames(held_segments)
    if id_frames:
        held_object, idents = lib.identify_held_object(ep, backend, id_frames, workdir, max_frames=idc["max_frames"], scale=idc["scale"],
                                                       temperature=idc["temperature"], glossary=lib.episode_glossary(ep), log=log)
    events = events_from_held_segments(ep, held_segments, held_object)
    states = frame_states(n, segments, judgments, vcfg.get("held_obs_judged_frames", "vlm"))

    nc = ep.n_chunks
    prediction = {
        "held_obs": [{"frame": int(i), "state": states[i], "object": None} for i in range(n)],
        "events": events, "held_object": held_object,
        "chunk_labels": [None] * nc, "chunk_q": [0.0] * nc, "decisive_chunk": None, "cause": None,
    }
    evidence = {
        "close_runs": close_runs(cmd, int(ccfg["close_min_run"])),
        "candidates": segments,
        "judged_frames": frames,
        "judgments": [{"frame": f, **judgments[f]} for f in frames],
        "held_segments": held_segments,
        "events": events,
        "identify_frames": lib.pick_frames(id_frames, idc["max_frames"]) if id_frames else [],
        "identify": idents,
        "n_candidates": len(segments), "n_judged": len(judged), "n_held_segments": len(held_segments),
    }
    v2.complete(ep, cfg, prediction, evidence, [])
    prediction.update(log.as_dict())
    prediction["raw_dir"] = str(workdir)
    prediction["protocol_s"] = round(time.time() - t0, 1)
    dump_json({"config": cfg, "prediction": prediction, "evidence": evidence}, workdir / "result.json")
    return prediction

CONFIG["completion"]["never_held_cause_reaching"] = True  # never held, no close-on-nothing, no wrong-object evidence -> reaching
