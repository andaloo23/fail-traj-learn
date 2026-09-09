"""Blinded, observable-event experiment; no outcome, telemetry, diagnosis or reference in model inputs.

python event_experiment.py DATASET EPISODE --tag event_qwen_v1 --local 10 13 --run
Without --run, only export identical image/prompt bundles for manual or alternate-model comparison.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image
import numpy as np

from common import Episode, WIN_OUT, dump_json, open_dataset
from schema import ParseError, extract_json


VERSION = "events_v1"
SYSTEM = """Describe observable changes in a short sequence of robot camera observations.
Each image contains agent camera on the left and wrist camera on the right, at its exact stated frame.
Describe appearance, not inferred task identity. Do not infer causes, success, failure, intent, or recoverability.
An object close to the fingers is not necessarily held. Check its relationship to the fingers across images.
Report attachment/detachment only when the images support that transition; otherwise use uncertain.
Do not invent changes: windows with no supported transition should have an empty events list.
Use only frame numbers supplied in this window. last_before_frame and first_after_frame bracket the change,
not an imagined exact event frame. Use null endpoints if the transition is obscured or outside the window.
Return only this JSON structure:
{"status":"observed|no_change|uncertain", "held_object":"appearance description or null",
 "evidence":"brief concrete visual evidence", "events":[
 {"type":"attachment|detachment|other_change", "object":"appearance description or null",
 "last_before_frame":null, "first_after_frame":null, "description":"visible change"}]}
For a detachment, last_before_frame is the last observation clearly held, first_after_frame the first clearly
detached. For attachment, bracket the reverse transition. Report all supported changes in the window.
"""


def window_plan(n_chunks, width=4, overlap=2):
    if width < 1 or not 0 <= overlap < width:
        raise ValueError("require width > overlap >= 0")
    if n_chunks <= width:
        return [(0, n_chunks - 1)]
    starts = list(range(0, n_chunks - width + 1, width - overlap))
    if starts[-1] != n_chunks - width:
        starts.append(n_chunks - width)
    return [(s, s + width - 1) for s in starts]


def sampled_frames(chunks, lo, hi, stride):
    if stride < 1 or not 0 <= lo <= hi < len(chunks):
        raise ValueError("invalid frame stride or chunk window")
    return sorted(set(range(chunks[lo][0], chunks[hi][1], stride)) |
                  {f for c in range(lo, hi + 1) for f in (chunks[c][0], chunks[c][1] - 1)})


def parse_events(raw, frames):
    d = json.loads(extract_json(raw))
    if not isinstance(d, dict) or d.get("status") not in ("observed", "no_change", "uncertain"):
        raise ValueError("invalid status")
    if not isinstance(d.get("events"), list):
        raise ValueError("events must be a list")
    for key in ("held_object", "evidence"):
        if d.get(key) is not None and not isinstance(d[key], str):
            raise ValueError(f"invalid {key}")
    for event in d["events"]:
        if not isinstance(event, dict) or event.get("type") not in ("attachment", "detachment", "other_change"):
            raise ValueError("invalid event type")
        for key in ("last_before_frame", "first_after_frame"):
            value = event.get(key)
            if value is not None and (type(value) is not int or value not in frames):
                raise ValueError(f"{key} is not a supplied frame")
        a, b = event.get("last_before_frame"), event.get("first_after_frame")
        if a is not None and b is not None and a >= b:
            raise ValueError("event endpoints must be ordered")
    if d["status"] == "no_change" and d["events"]:
        raise ValueError("no_change contradicts events")
    if d["status"] == "observed" and not d["events"]:
        raise ValueError("observed requires an event")
    return d


def export_window(ep, lo, hi, stride, out):
    frames = sampled_frames(ep.chunks, lo, hi, stride)
    out.mkdir(parents=True, exist_ok=True)
    blocks = [{"type": "text", "text": "Describe only the observable events in these time-ordered images."}]
    digest = hashlib.sha256(SYSTEM.encode())
    for i in frames:
        agent, wrist = ep.frame(i)
        # Native 256x256 cameras; no resize, no hidden chunks, no burned-in occlusion.
        im = Image.fromarray(np.concatenate([agent, wrist], axis=1))
        name = f"frame_{i:06d}.png"
        im.save(out / name)
        caption = f"Frame {i}; time {i / ep.fps:.3f} seconds; agent left, wrist right."
        blocks.extend([{"type": "text", "text": caption}, {"type": "image", "path": name}])
        digest.update(caption.encode())
        digest.update(im.tobytes())
    bundle = {"version": VERSION, "system": SYSTEM, "content": blocks, "frames": frames,
              "input_sha256": digest.hexdigest()}
    dump_json(bundle, out / "input.json")
    return bundle


def summarize(results, reference, chunks):
    """Reference is consulted only after inference. Its coverage is explicitly partial."""
    candidates = []
    for row in results:
        for event in row.get("parsed", {}).get("events", []):
            if event["type"] == "detachment":
                candidates.append({"window": row["window"], **event})
    summary = {"windows": len(results), "valid_windows": sum("parsed" in r for r in results),
               "invalid_windows": [{"window": r["window"], "error": r.get("error")} for r in results if "parsed" not in r],
               "detachment_candidates": candidates,
               "note": "Overlapping-window candidates are not independent events. Unreviewed candidates are not false alarms."}
    if reference:
        lo, hi = chunks[reference["chunk"]]
        matches = [e for e in candidates if e.get("last_before_frame") is not None and
                   e.get("first_after_frame") is not None and e["last_before_frame"] < hi and e["first_after_frame"] >= lo]
        summary["reference_check"] = {"reference": reference, "frame_range_inclusive": [lo, hi - 1],
                                      "matching_brackets": matches,
                                      "any_bracket_overlaps_reference_chunk": bool(matches),
                                      "caution": "Chunk-level overlap does not verify exact timing, object identity, or cause."}
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset")
    ap.add_argument("episode", type=int)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--local", nargs=2, type=int, default=[10, 13])
    ap.add_argument("--width", type=int, default=4)
    ap.add_argument("--overlap", type=int, default=2)
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--model", default="Qwen/Qwen3-VL-8B-Instruct")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--reference", type=Path)
    args = ap.parse_args()
    ep = Episode(open_dataset(args.dataset), args.dataset, args.episode)
    scan = window_plan(ep.n_chunks, args.width, args.overlap)
    local = tuple(args.local)
    windows = list(dict.fromkeys([local] + scan))
    root = WIN_OUT / "event_experiments" / args.tag / args.dataset / f"ep{args.episode:04d}"
    config = {"version": VERSION, "dataset": args.dataset, "episode": args.episode, "model": args.model,
              "local": list(local), "width": args.width, "overlap": args.overlap, "stride": args.stride,
              "temperature": 0.0, "k": 1, "max_new_tokens": 1000}
    config_path = root / "config.json"
    if config_path.exists() and json.loads(config_path.read_text()) != config:
        raise ValueError("configuration changed: use a new tag")
    dump_json(config, config_path)
    backend = None
    results = []
    for lo, hi in windows:
        path = root / f"window_{lo:03d}_{hi:03d}"
        bundle = export_window(ep, lo, hi, args.stride, path)
        result_path = path / "response.json"
        if result_path.exists():
            row = json.loads(result_path.read_text())
            if row["input_sha256"] != bundle["input_sha256"]:
                raise ValueError("input changed: use a new tag")
            results.append(row)
            continue
        if not args.run:
            continue
        if backend is None:
            from backend_qwen import QwenBackend
            backend = QwenBackend(args.model)
        content = [({"type": "image", "image": Image.open(path / b["path"]).convert("RGB")}
                    if b["type"] == "image" else b) for b in bundle["content"]]
        raw = backend.generate(SYSTEM, content, k=1, temperature=0.0, max_new_tokens=1000, batch=1)[0]
        row = {"window": [lo, hi], "frames": bundle["frames"], "input_sha256": bundle["input_sha256"],
               "model": args.model, "raw": raw, "generation": dict(backend.last)}
        try:
            row["parsed"] = parse_events(raw, bundle["frames"])
        except (ValueError, TypeError, KeyError, ParseError) as exc:
            row["error"] = str(exc)
        dump_json(row, result_path)
        results.append(row)
        print(f"window {lo}-{hi}: {row.get('parsed', {}).get('status', 'invalid')} {row.get('parsed', {}).get('events', [])}", flush=True)
    reference = None
    if args.reference:
        reference = json.loads(args.reference.read_text())
        if (reference["dataset"], reference["episode"]) != (args.dataset, args.episode):
            raise ValueError("reference belongs to another episode")
    report = {"config": config, "local": summarize([r for r in results if tuple(r["window"]) == local], reference, ep.chunks),
              "scan": summarize([r for r in results if tuple(r["window"]) in scan], reference, ep.chunks),
              "planned_scan_windows": len(scan), "completed_windows": len(results)}
    dump_json(report, root / "report.json")
    cards = []
    for row in results:
        lo, hi = row["window"]
        folder = f"window_{lo:03d}_{hi:03d}"
        cards.append(f'<h2>Chunks {lo}-{hi}</h2><p><a href="{folder}/input.json">Exact input</a> | '
                     f'<a href="{folder}/response.json">Raw response and timing</a></p><pre>' +
                     html.escape(json.dumps(row.get("parsed", row.get("error")), indent=2)) + '</pre>' +
                     ''.join(f'<figure><img loading="lazy" src="{folder}/frame_{i:06d}.png"><figcaption>Frame {i}</figcaption></figure>'
                             for i in row["frames"]))
    (root / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>Event experiment</title>'
        '<style>body{background:#121923;color:#e1e8f2;font:16px system-ui;margin:30px}a{color:#86d2ff}'
        'pre{white-space:pre-wrap}figure{display:inline-block;margin:6px}img{width:512px;max-width:100%}h2{border-top:1px solid #777;padding-top:24px}</style>'
        '<h1>Blinded event detection</h1><p>Inputs contain camera frames and timestamps only. Predictions are unverified. '
        'Local window selection is human-assisted; the scan uses fixed windows. Their shared window is evaluated once and reused.</p>'
        '<pre>' + html.escape(json.dumps(report, indent=2)) + '</pre>' + ''.join(cards))
    print(f"EXPERIMENT_OK {root}", flush=True)


if __name__ == "__main__":
    main()
