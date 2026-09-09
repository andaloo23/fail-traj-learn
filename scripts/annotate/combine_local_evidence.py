"""Combine experimental local labels with independent Qwen frame states; never reads oracle columns.

The result is a review artifact, not verified training labels. No causal root-error time is assigned.
"""
import argparse
from collections import Counter, defaultdict
import json

import numpy as np

from common import Episode, WIN_OUT, dump_json, open_dataset


def consensus_frames(records):
    votes = defaultdict(list)
    for row in records:
        for item in row.get("parsed", {}).get("states", []):
            votes[item["frame"]].append(item["state"])
    out = []
    for frame, labels in sorted(votes.items()):
        state, count = Counter(labels).most_common(1)[0]
        out.append({"frame": frame, "state": state if count * 2 > len(labels) else "uncertain",
                    "support": count / len(labels), "votes": dict(Counter(labels))})
    return out


def transitions(states, min_run=2):
    """Confirm a changed state only after consecutive observations; keep isolated disagreements in raw data."""
    stable = None
    last_stable = None
    pending = []
    events = []
    for item in states:
        state = item["state"]
        if state == "uncertain":
            pending = []
            continue
        if state == stable:
            last_stable = item
            pending = []
            continue
        if pending and pending[0]["state"] != state:
            pending = []
        pending.append(item)
        if len(pending) < min_run:
            continue
        if stable is not None:
            events.append({"event": "loss_or_release" if stable == "held" else "grasp",
                           "last_before_frame": last_stable["frame"], "first_after_frame": pending[0]["frame"],
                           "support": min(x["support"] for x in [last_stable] + pending)})
        stable, last_stable, pending = state, item, []
    return events


def agree_events(tracks, refinement=()):
    """Agree on events across independently sampled tracks BEFORE merging any frame observations."""
    proposals = {tag: transitions(states) for tag, states in tracks.items()}
    out = {}
    for tag, candidates in proposals.items():
        for event in candidates:
            matches = {tag: event}
            lo, hi = event["last_before_frame"], event["first_after_frame"]
            for other_tag, other_events in proposals.items():
                if other_tag == tag:
                    continue
                overlapping = [e for e in other_events if e["event"] == event["event"] and
                               e["last_before_frame"] < hi and e["first_after_frame"] > lo]
                if overlapping:
                    other = min(overlapping, key=lambda e: e["first_after_frame"] - e["last_before_frame"])
                    matches[other_tag] = other
                    lo = max(lo, other["last_before_frame"])
                    hi = min(hi, other["first_after_frame"])
            if len(matches) < min(2, len(tracks)):
                continue
            key = (event["event"], lo, hi)
            out[key] = {"event": event["event"], "last_before_frame": lo, "first_after_frame": hi,
                        "source_tracks": sorted(matches), "coarse_brackets": matches, "support": 1.0}
    for event in out.values():
        lo, hi = event["last_before_frame"], event["first_after_frame"]
        before_state, after_state = ("held", "empty") if event["event"] == "loss_or_release" else ("empty", "held")
        nearby = [s for s in refinement if lo <= s["frame"] <= hi + 2]
        for i, first in enumerate(nearby[:-1]):
            second = nearby[i + 1]
            if first["frame"] > hi or first["state"] != after_state or second["state"] != after_state:
                continue
            before = [s for s in nearby[:i] if s["state"] == before_state]
            if before:
                event["last_before_frame"] = before[-1]["frame"]
                event["first_after_frame"] = first["frame"]
                event["refined"] = True
                break
    return sorted(out.values(), key=lambda e: e["first_after_frame"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="full_shift8__t0")
    ap.add_argument("--episode", type=int, default=0)
    ap.add_argument("--states-tags", nargs="+", default=["lab_v5_full"])
    ap.add_argument("--refinement-tags", nargs="*", default=[])
    ap.add_argument("--local-tag", default="local_v2")
    ap.add_argument("--context-tag", default="local_v2_context5")
    ap.add_argument("--out-tag", default="event_first_review")
    args = ap.parse_args()
    ep = Episode(open_dataset(args.dataset), args.dataset, args.episode)
    def root(tag):
        return WIN_OUT / "segmentation_lab" / tag / args.dataset / f"ep{args.episode:04d}"
    rows = []
    tracks = {}
    for tag in args.states_tags:
        track_rows = []
        for path in sorted(root(tag).glob("state_*.json")):
            row = json.loads(path.read_text())
            if len(row["frames"]) != 1:
                raise ValueError("Only independent single-frame observations can be combined here")
            rows.append(row)
            track_rows.append(row)
        tracks[tag] = consensus_frames(track_rows)
    refined_rows = [json.loads(p.read_text()) for tag in args.refinement_tags for p in root(tag).glob("state_*.json")]
    states = consensus_frames(rows + refined_rows)
    events = agree_events(tracks, consensus_frames(refined_rows))
    local = {r["chunk"]: r for path in root(args.local_tag).glob("chunk_*.json") for r in [json.loads(path.read_text())]}
    context = {r["chunk"]: r for path in root(args.context_tag).glob("chunk_*.json") for r in [json.loads(path.read_text())]}
    result = []
    for c, (a, b) in enumerate(ep.chunks):
        prediction = local.get(c, {})
        label = prediction.get("label", "uncertain")
        notes = []
        provenance = "local_vlm"
        if c in context and context[c]["label"] != label:
            notes.append("local_label_changes_with_context")
            label = "uncertain"
        recent = [e for e in events if e["first_after_frame"] <= a]
        prior_grasp = any(e["event"] == "grasp" and e["first_after_frame"] <= a for e in events)
        path_cm = float(np.linalg.norm(np.diff(ep.eef_xyz[a:min(ep.n, b + 1)], axis=0), axis=1).sum() * 100)
        # Do not silently discard a potentially productive approach as neutral solely because nothing is held.
        if label == "neutral" and not prior_grasp and path_cm > 2:
            notes.append("moving_before_grasp_task_alignment_unverified")
            label = "uncertain"
        observations = [s.get("parsed", {}).get("observation", "").lower() for s in prediction.get("samples", [])]
        if path_cm > 2 and sum("stationary" in o for o in observations) >= 2:
            notes.append("stationary_description_contradicts_proprioception")
            label = "uncertain"
        # Retain the distinction between a correct label and an unsupported narrative of holding.
        points = [s for s in states if a <= s["frame"] <= b]
        if points and all(s["state"] == "empty" for s in points) and any("holding" in o or "holds" in o for o in observations):
            notes.append("holding_description_contradicts_frame_observations")
            label = "uncertain"
        for event in events:
            before, after = event["last_before_frame"], event["first_after_frame"]
            # Transition actions are bracketed by before .. after-1. Do not assign across chunk boundaries.
            if event["event"] != "loss_or_release" or not (before < b and after > a):
                continue
            if before < a or after > b:
                notes.append("transition_bracket_spans_chunks_needs_refinement")
                label = "uncertain"
                continue
            command = ep.gripper_cmd[before:after]
            if len(command) and np.all(command > 0.5):
                label = "failure_inducing"
                provenance = "independent_visual_loss_plus_close_command"
                notes.append("observed_loss_not_causal_root_error")
            else:
                notes.append("release_intent_unresolved")
        result.append({"chunk": c, "label": label, "local_label": prediction.get("label"),
                       "context_label": context.get(c, {}).get("label"), "provenance": provenance,
                       "notes": notes, "training_q": 0.0})
    segments = []
    for item in result:
        if segments and segments[-1]["label"] == item["label"]:
            segments[-1]["end"] = item["chunk"]
        else:
            segments.append({"start": item["chunk"], "end": item["chunk"], "label": item["label"]})
    output = {"settings": vars(args), "states": states, "tracks": tracks, "events": events, "chunks": result, "segments": segments,
              "decisive_error": None, "warning": "Experimental, reviewed-example development only; no generalization claim. All training weights remain zero."}
    dump_json(output, root(args.out_tag) / "result.json")
    print(json.dumps({"events": events, "segments": segments}, indent=2))


if __name__ == "__main__":
    main()
