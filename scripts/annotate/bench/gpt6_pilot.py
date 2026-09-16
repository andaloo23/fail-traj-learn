"""Prepare, freeze, and privileged-state-check the GPT-6 observable-label pilot.

The annotator works only from ``public_manifest.json`` and ``visual/<id>``. The
private identity map and oracle references are read only by ``verify`` after the
authored file has been hash-frozen.

Examples:
  python gpt6_pilot.py select --n 30
  python gpt6_pilot.py prepare
  python gpt6_pilot.py validate
  python gpt6_pilot.py freeze
  python gpt6_pilot.py verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from common import Episode, PROJ, open_dataset  # noqa: E402
from review_oracle import decode_episode  # noqa: E402

OUT = ROOT / "outputs" / "gpt6_pilot_v1"
REFS = PROJ / "bench" / "references"
TAXONOMY_PATH = HERE / "gpt6_taxonomy_v1.json"
TOLERANCE_CHUNKS = 1
RECOVERY_HORIZON_CHUNKS = 3


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def references():
    rows = []
    for path in sorted(REFS.glob("*/episode_*.json")):
        row = read_json(path)
        if row.get("reference_version") == "r6" and row.get("failure_mode") != "other":
            rows.append(row)
    return rows


def balanced_sample(rows, n, seed):
    """Twenty-four failures across modes plus six successes when n=30."""
    rng = random.Random(seed)
    failures = [r for r in rows if not r["success"]]
    successes = [r for r in rows if r["success"]]
    n_success = max(1, n // 5)
    n_failure = n - n_success
    by_mode = defaultdict(list)
    for row in failures:
        by_mode[row["failure_mode"]].append(row)
    for group in by_mode.values():
        rng.shuffle(group)
    modes = sorted(by_mode)
    chosen = []
    # Round-robin gives rare modes representation before frequent modes fill slots.
    while len(chosen) < n_failure and any(by_mode.values()):
        for mode in modes:
            if by_mode[mode] and len(chosen) < n_failure:
                chosen.append(by_mode[mode].pop())
    # Spread successes over task identities.
    rng.shuffle(successes)
    seen_tasks = set()
    success_chosen = []
    for row in successes:
        key = (row["suite"], row["task_id"])
        if key not in seen_tasks:
            success_chosen.append(row)
            seen_tasks.add(key)
        if len(success_chosen) == n_success:
            break
    chosen += success_chosen
    rng.shuffle(chosen)
    return chosen


def select(args):
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "freeze.json").exists():
        raise RuntimeError("pilot is frozen; choose a new output/version")
    chosen = balanced_sample(references(), args.n, args.seed)
    private, public = [], []
    for i, row in enumerate(chosen, 1):
        ident = f"P{i:03d}"
        private.append({"id": ident, "dataset": row["dataset"], "episode_index": row["episode_index"],
                        "stratum": "success" if row["success"] else row["failure_mode"]})
        public.append({"id": ident, "task": row["task"], "n_frames": row["n_frames"], "fps": row["fps"],
                       "frame_bounds": "zero-based, end-exclusive"})
    write_json(OUT / "private_manifest.json", private)
    write_json(OUT / "public_manifest.json", public)
    taxonomy = read_json(TAXONOMY_PATH)
    write_json(OUT / "authored.template.json", {
        "version": "gpt6_pilot_v1", "taxonomy_version": taxonomy["version"],
        "input_policy": "paired cameras, task text, measured robot state and gripper command; no outcome or priv.*",
        "episodes": [{"id": p["id"], "summary": "", "segments": []} for p in public]
    })
    print(json.dumps({"episodes": len(chosen), "private_strata": dict(Counter(x["stratum"] for x in private))}, indent=2))


def contact_sheet(agent, wrist, frames, path):
    thumb_w, thumb_h, cols = 384, 216, 4
    rows = (len(frames) + cols - 1) // cols
    canvas = Image.new("RGB", (thumb_w * cols, thumb_h * rows), "white")
    draw = ImageDraw.Draw(canvas)
    for j, frame in enumerate(frames):
        pair = Image.fromarray(np.concatenate([agent[frame], wrist[frame]], axis=1)).resize((thumb_w, 192))
        x, y = (j % cols) * thumb_w, (j // cols) * thumb_h
        canvas.paste(pair, (x, y + 24))
        draw.text((x + 5, y + 5), f"frame {frame}", fill="black")
    canvas.save(path, quality=92)


def prepare(_args):
    private = read_json(OUT / "private_manifest.json")
    public = {x["id"]: x for x in read_json(OUT / "public_manifest.json")}
    datasets = {}
    for entry in private:
        if entry["dataset"] not in datasets:
            datasets[entry["dataset"]] = open_dataset(entry["dataset"])
        ds = datasets[entry["dataset"]]
        ep = Episode(ds, entry["dataset"], entry["episode_index"])
        agent, wrist, _ = decode_episode(ds, ep)
        folder = OUT / "visual" / entry["id"]
        folder.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(folder / "cameras.npz", agent=agent, wrist=wrist)
        # 32 overview observations, with adjacent frames available for later refinement.
        frames = sorted(set(np.linspace(0, ep.n - 1, min(32, ep.n), dtype=int).tolist()))
        contact_sheet(agent, wrist, frames, folder / "overview.jpg")
        state, action = ep.col("observation.state"), ep.col("action")
        telemetry = [{"frame": i, "eef_xyz_m": state[i, :3].round(5).tolist(),
                      "finger_qpos_m": state[i, 6:8].round(5).tolist(),
                      "gripper_command": "close" if action[i, 6] > 0 else "open"} for i in range(ep.n)]
        write_json(folder / "observable.json", {
            **public[entry["id"]], "sampled_frames": frames,
            "notes": "Finger positions and command are not proof of contact or possession.", "telemetry": telemetry
        })
        print(entry["id"], ep.n, flush=True)


def validate_authored(data):
    taxonomy = read_json(TAXONOMY_PATH)
    public = read_json(OUT / "public_manifest.json")
    meta = {x["id"]: x for x in public}
    assert data["taxonomy_version"] == taxonomy["version"]
    assert [e["id"] for e in data["episodes"]] == [e["id"] for e in public]
    vocab = {k: set(taxonomy[k]) if isinstance(taxonomy[k], dict) else set(taxonomy[k])
             for k in ("roles", "events", "failure_families", "failure_subtypes", "task_stages", "object_relations", "recovery_states")}
    for episode in data["episodes"]:
        previous = -1
        for seg in episode["segments"]:
            assert 0 <= seg["start_frame"] < seg["end_frame_exclusive"] <= meta[episode["id"]]["n_frames"]
            assert seg["start_frame"] >= previous, f"overlap or unsorted segment in {episode['id']}"
            previous = seg["end_frame_exclusive"]
            for key in ("roles", "events", "failure_families", "failure_subtypes", "task_stages"):
                assert isinstance(seg.get(key), list) and set(seg[key]) <= vocab[key], (episode["id"], key)
            assert seg["object_relation"] in vocab["object_relations"]
            assert seg["recovery_state"] in vocab["recovery_states"]
            assert 0 <= float(seg["confidence"]) <= 1
            assert seg.get("rationale")
            assert set(seg.get("evidence_frames", [])) <= set(range(meta[episode["id"]]["n_frames"]))
            assert set(seg.get("interval_kind", [])) <= {"attempt", "observed_event", "suspected_contribution"}
    return data


def validate(_args):
    data = validate_authored(read_json(OUT / "authored.json"))
    print(f"valid: {len(data['episodes'])} episodes, {sum(len(e['segments']) for e in data['episodes'])} segments")


def freeze(_args):
    path = OUT / "authored.json"
    validate_authored(read_json(path))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(OUT / "freeze.json", {"authored_sha256": digest, "oracle_access_after_freeze": False})
    print(digest)


def overlaps(a, b, c, d, tolerance=0):
    return a < d + tolerance and c < b + tolerance


def event_intervals(ref, kind):
    chunks = ref["chunks"]
    out = []
    if kind in {"grasp_acquisition", "release", "slip_drop"}:
        mapped = {"grasp_acquisition": "grasp", "release": "release", "slip_drop": "drop"}[kind]
        out = [(e["last_before"], e["first_after"] + 1) for e in ref["events"] if e["type"] == mapped]
    elif kind == "failed_grasp":
        out = [(x["start"], x["end"] + 1) for x in ref.get("close_on_nothing", [])]
        for attempt in ref.get("attempts", []):
            if attempt.get("outcome") in {"miss", "slip"}:
                out.append((attempt["start"], attempt["end"] + 1))
    elif kind == "collision":
        out = [(x["start"], x["end"] + 1) for x in ref.get("collisions", [])]
    elif kind == "wrong_object_interaction":
        out = [(x["start"], x["end"] + 1) for x in ref.get("wrong_object_contacts", [])]
    elif kind == "placement":
        f = ref["stage_frames"].get("placed", -1)
        out = [] if f < 0 else [(f, f + 1)]
    return out


def held_overlap(ref, start, end, target_only=True):
    for run in ref["held_runs"]:
        if run["state"] != "held" or (target_only and run.get("object") != ref.get("target_slot")):
            continue
        if overlaps(start, end, run["start"], run["end"] + 1):
            return True
    return False


def check_claim(ref, seg, head, label):
    start, end = seg["start_frame"], seg["end_frame_exclusive"]
    tol = TOLERANCE_CHUNKS * 10
    intervals = event_intervals(ref, label) if head == "events" else []
    if intervals:
        return ("supported" if any(overlaps(start, end, a, b, tol) for a, b in intervals) else "contradicted",
                f"nearest privileged {label} interval")
    if head == "events" and label in {"grasp_acquisition", "release", "slip_drop", "failed_grasp", "collision", "wrong_object_interaction", "placement"}:
        return "contradicted", f"no privileged {label} event within tolerance"
    if head == "events" and label == "controlled_transport":
        transported = ref["stage_frames"].get("transported", -1)
        ok = held_overlap(ref, start, end) and (transported >= 0 or ref["stage_frames"].get("lifted", -1) >= 0)
        return ("supported" if ok else "contradicted"), "target hold plus lift/transport state"
    if head == "roles" and label == "task_progress":
        stages = [f for f in ref["stage_frames"].values() if isinstance(f, int) and f >= 0]
        ok = any(start - tol <= f < end + tol for f in stages) or held_overlap(ref, start, end)
        return ("supported" if ok else "indeterminate"), "stage transition or target hold"
    if head == "roles" and label == "physical_failure":
        facts = sum((event_intervals(ref, k) for k in ("slip_drop", "failed_grasp", "collision", "wrong_object_interaction")), [])
        return ("supported" if any(overlaps(start, end, a, b, tol) for a, b in facts) else "contradicted"), "physical event proximity"
    if head == "roles" and label == "recovery_success":
        errors = sum((event_intervals(ref, k) for k in ("slip_drop", "failed_grasp")), [])
        grasps = event_intervals(ref, "grasp_acquisition")
        ok = any(e[1] <= g[0] <= end + tol and g[0] >= start - tol for e in errors for g in grasps)
        return ("supported" if ok else "contradicted"), "re-grasp after physical error"
    if head == "failure_subtypes" and label == "transport.collision_with_drop":
        cs, ds = event_intervals(ref, "collision"), event_intervals(ref, "slip_drop")
        ok = any(c[0] <= d[0] <= c[1] + RECOVERY_HORIZON_CHUNKS * 10 for c in cs for d in ds)
        return ("supported" if ok else "contradicted"), "collision followed by target drop"
    if head == "failure_subtypes" and label == "sequencing_semantic.wrong_object":
        ok = bool(event_intervals(ref, "wrong_object_interaction"))
        return ("supported" if ok else "contradicted"), "non-target gripper contact"
    if head == "failure_subtypes" and label == "placement_release.no_release":
        return ("supported" if ref["failure_mode"] == "hold_no_release" else "contradicted"), "held-at-end outcome"
    if head == "failure_families":
        family_map = {"never_reached": "reaching", "missed_grasp": "grasping", "drop_transport": "transport",
                      "release_miss": "placement_release", "hold_no_release": "placement_release",
                      "wrong_object": "sequencing_semantic", "collision": "collision", "stall_after_grasp": "manipulation"}
        expected = family_map.get(ref["failure_mode"])
        if expected == label:
            return "supported", "episode physical failure mode agrees"
        return "indeterminate", f"oracle episode mode maps to {expected or 'none'}"
    if head == "task_stages":
        f = ref["stage_frames"].get(label, -1)
        if label == "placed":
            ok = f >= 0 and start - tol <= f < end + tol
        elif label in {"grasped", "lifted", "transported"}:
            # These labels describe a stage achieved or active in the interval, not necessarily
            # the exact transition frame. Target possession prevents a prior, later-lost stage
            # from supporting an unrelated segment.
            ok = f >= 0 and f < end + tol and held_overlap(ref, start, end)
        else:
            ok = f >= 0 and f < end + tol
        return ("supported" if ok else "contradicted"), "stage achieved/active in interval"
    return "indeterminate", "privileged record does not resolve this claim"


def verify(_args):
    freeze_path, authored_path = OUT / "freeze.json", OUT / "authored.json"
    frozen = read_json(freeze_path)
    digest = hashlib.sha256(authored_path.read_bytes()).hexdigest()
    if digest != frozen["authored_sha256"]:
        raise RuntimeError("authored labels changed after freeze")
    authored = validate_authored(read_json(authored_path))
    private = {x["id"]: x for x in read_json(OUT / "private_manifest.json")}
    results, counts, coverage_rows = [], Counter(), []
    for episode in authored["episodes"]:
        ident = private[episode["id"]]
        path = REFS / ident["dataset"] / f"episode_{ident['episode_index']:06d}.json"
        ref = read_json(path)
        for j, seg in enumerate(episode["segments"]):
            for head in ("roles", "events", "failure_families", "failure_subtypes", "task_stages"):
                for label in seg[head]:
                    status, basis = check_claim(ref, seg, head, label)
                    counts[(head, label, status)] += 1
                    results.append({"id": episode["id"], "segment_index": j, "start_frame": seg["start_frame"],
                                    "end_frame_exclusive": seg["end_frame_exclusive"], "head": head,
                                    "label": label, "status": status, "basis": basis})
        # Reverse check: every objective reference event must be discoverable, including episodes
        # on which the sparse annotator emitted nothing. This is coverage, not semantic recall.
        predicted = [(s["start_frame"], s["end_frame_exclusive"], label)
                     for s in episode["segments"] for label in s["events"]]
        inventory = []
        for label in ("grasp_acquisition", "release", "slip_drop", "failed_grasp", "collision", "wrong_object_interaction", "placement"):
            inventory += [(label, a, b) for a, b in event_intervals(ref, label)]
        for label, a, b in inventory:
            matched = any(plabel == label and overlaps(a, b, pa, pb, TOLERANCE_CHUNKS * 10)
                          for pa, pb, plabel in predicted)
            coverage_rows.append({"id": episode["id"], "event": label, "start_frame": a,
                                  "end_frame_exclusive": b, "covered": matched})
    summary = []
    keys = sorted({(h, l) for h, l, _ in counts})
    for head, label in keys:
        row = {s: counts[(head, label, s)] for s in ("supported", "contradicted", "indeterminate")}
        row.update(head=head, label=label, total=sum(row.values()))
        summary.append(row)
    write_json(OUT / "verification" / "claims.json", results)
    coverage_counts = Counter((x["event"], x["covered"]) for x in coverage_rows)
    coverage = [{"event": label, "covered": coverage_counts[(label, True)],
                 "total": coverage_counts[(label, True)] + coverage_counts[(label, False)]}
                for label in sorted({x["event"] for x in coverage_rows})]
    by_claim = {(r["id"], r["segment_index"], r["head"], r["label"]): r for r in results}
    candidates = []
    for episode in authored["episodes"]:
        for j, seg in enumerate(episode["segments"]):
            targets = {}
            for head in ("roles", "events", "failure_families", "failure_subtypes", "task_stages"):
                targets[head] = []
                for label in seg[head]:
                    claim = by_claim[(episode["id"], j, head, label)]
                    targets[head].append({"label": label, "verification": claim["status"],
                                          "loss_mask": claim["status"] == "supported",
                                          "loss_weight": float(seg["confidence"]) if claim["status"] == "supported" else 0.0})
            candidates.append({"id": episode["id"], "segment_index": j,
                               "start_frame": seg["start_frame"], "end_frame_exclusive": seg["end_frame_exclusive"],
                               "annotation_confidence": seg["confidence"], "targets": targets})
    write_json(OUT / "verification" / "event_coverage.json", coverage_rows)
    write_json(OUT / "training_candidates.json", {
        "version": "gpt6_pilot_v1_verified_candidates", "taxonomy_version": authored["taxonomy_version"],
        "policy": "Only supported positive claims have loss_mask=true; absent, contradicted, and indeterminate claims are masked.",
        "segments": candidates
    })
    write_json(OUT / "verification" / "summary.json", {
        "authored_sha256": digest, "reference_version": "r6", "tolerance_chunks": TOLERANCE_CHUNKS,
        "scope": "physical support, not causal correctness", "claims": summary, "event_coverage": coverage
    })
    frozen["oracle_access_after_freeze"] = True
    write_json(freeze_path, frozen)
    supported = sum(x["supported"] for x in summary)
    contradicted = sum(x["contradicted"] for x in summary)
    indeterminate = sum(x["indeterminate"] for x in summary)
    report = ["# GPT-6 observable-label pilot v1", "",
              f"Frozen annotations: `{digest}`", "",
              f"30 episodes, {len(candidates)} sparse segments. Claim checks: {supported} supported, "
              f"{contradicted} contradicted, {indeterminate} indeterminate.", "",
              "This is physical-evidence verification, not causal validation. Contradicted and indeterminate claims receive zero loss weight.", "",
              "## Claim checks", "", "| Head | Label | Supported | Contradicted | Indeterminate |", "|---|---|---:|---:|---:|"]
    report += [f"| {x['head']} | {x['label']} | {x['supported']} | {x['contradicted']} | {x['indeterminate']} |" for x in summary]
    report += ["", "## Objective-event coverage", "", "| Event | Covered | Total |", "|---|---:|---:|"]
    report += [f"| {x['event']} | {x['covered']} | {x['total']} |" for x in coverage]
    report += ["", "Coverage is intentionally reported separately: sparse high-confidence annotations missed many physical events.", ""]
    (OUT / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("select"); p.add_argument("--n", type=int, default=30); p.add_argument("--seed", type=int, default=20260915); p.set_defaults(fn=select)
    sub.add_parser("prepare").set_defaults(fn=prepare)
    sub.add_parser("validate").set_defaults(fn=validate)
    sub.add_parser("freeze").set_defaults(fn=freeze)
    sub.add_parser("verify").set_defaults(fn=verify)
    args = parser.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
