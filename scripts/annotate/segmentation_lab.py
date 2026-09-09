"""Controlled Qwen ablations. Oracle columns are used only by score(), after model calls.

Run: segmentation_lab.py --configs state_both state_agent state_wrist events_both events_agent
Follow-up: --configs state_agent --windows 9:12 11:14 12:13 --stride 1 --repeats 3
"""
import argparse
from collections import Counter
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image

from common import Episode, WIN_OUT, dump_json, open_dataset
from event_experiment import SYSTEM as EVENT_SYSTEM, parse_events, sampled_frames
from schema import extract_json


STATE_SYSTEM = """Inspect whether the robot is physically holding an external object in EACH image.
The white mechanical housing, white curved fingers and black finger pads are parts of the robot,
not a white cup or mug. An external object below or near the fingers is not necessarily held.
Use the object/finger relationship, not presence in the wrist image. Falling objects are not held.
For each supplied frame return held, empty, or uncertain. held means an external object is visibly
secured between the fingers; empty means no external object is secured; uncertain means occlusion or
ambiguous contact. Describe appearance, not an inferred task identity. Do not infer success or causes.
Output JSON only: {"states":[{"frame":<supplied integer>,"state":"held|empty|uncertain",
"object":"appearance or null"}]}. Include every supplied frame exactly once in order.
"""


def parse_states(raw, frames):
    d = json.loads(extract_json(raw))
    states = d.get("states", [])
    if [r.get("frame") for r in states] != frames:
        raise ValueError("states must cover exactly the input frames in order")
    if any(r.get("state") not in ("held", "empty", "uncertain") for r in states):
        raise ValueError("unknown holding state")
    return d


def content_for(ep, frames, camera, kind):
    description = {"both": "Each image has agent camera left and wrist camera right.",
                   "agent": "Each image is the external agent camera.",
                   "wrist": "Each image is the wrist-mounted camera."}[camera]
    content = [{"type": "text", "text": description + " Inspect these time-ordered observations."}]
    for i in frames:
        agent, wrist = ep.frame(i)
        array = np.concatenate([agent, wrist], axis=1) if camera == "both" else agent if camera == "agent" else wrist
        content.extend([{"type": "text", "text": f"Frame {i}, time {i / ep.fps:.3f}s:"},
                        {"type": "image", "image": Image.fromarray(array)}])
    system = STATE_SYSTEM if kind == "state" else EVENT_SYSTEM.replace(
        "Each image contains agent camera on the left and wrist camera on the right, at its exact stated frame.", description)
    return system, content


def score(ep, rows):
    """Physical-grasp audit, not a semantic ground-truth score. Unknown visual states reduce coverage."""
    grasp = ep.col("priv.obj_grasped").any(axis=1)
    contact = ep.col("priv.obj_gripper_contact").any(axis=1)
    groups = {}
    for row in rows:
        key = row["config"]
        g = groups.setdefault(key, {"queries": 0, "valid": 0, "frames": 0, "decided": 0,
                                   "correct": 0, "false_held": [], "missed_held": [], "events": []})
        g["queries"] += 1
        if "parsed" not in row:
            continue
        g["valid"] += 1
        for r in row["parsed"].get("states", []):
            i, s = r["frame"], r["state"]
            # Unilateral contact is physically ambiguous and should not set a binary reference.
            if contact[i] and not grasp[i]:
                continue
            g["frames"] += 1
            if s == "uncertain":
                continue
            g["decided"] += 1
            g["correct"] += int((s == "held") == bool(grasp[i]))
            if s == "held" and not grasp[i]:
                g["false_held"].append(i)
            if s == "empty" and grasp[i]:
                g["missed_held"].append(i)
        for e in row["parsed"].get("events", []):
            g["events"].append({"window": row["window"], **e})
    for g in groups.values():
        g["coverage"] = g["decided"] / g["frames"] if g["frames"] else None
        g["accuracy_on_decided"] = g["correct"] / g["decided"] if g["decided"] else None
    return groups


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", default="full_shift8__t0")
    p.add_argument("--episode", type=int, default=0)
    p.add_argument("--tag", default="lab_v1")
    p.add_argument("--configs", nargs="+", default=["state_both", "state_agent", "state_wrist", "events_both", "events_agent"])
    p.add_argument("--windows", nargs="+", default=["0:3", "8:11", "10:13", "12:15", "20:23"])
    p.add_argument("--stride", type=int, default=5)
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--frame-groups", nargs="+", help="Explicit comma-separated frames per independent query")
    p.add_argument("--native", action="store_true", help="Use standard Transformers generation to audit the custom cache backend")
    p.add_argument("--scale", type=float, default=1.0, help="Image enlargement / visual token allocation ablation")
    p.add_argument("--frame-stride", type=int, help="Independent single-frame queries across the entire episode")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--refine-from", help="Refine transition neighborhoods proposed by a saved independent-frame scan")
    args = p.parse_args()
    ep = Episode(open_dataset(args.dataset), args.dataset, args.episode)
    root = WIN_OUT / "segmentation_lab" / args.tag / args.dataset / f"ep{args.episode:04d}"
    windows = [tuple(map(int, w.split(":"))) for w in args.windows]
    plans = [(lo, hi, sampled_frames(ep.chunks, lo, hi, args.stride)) for lo, hi in windows]
    if args.frame_groups:
        plans = []
        for group in args.frame_groups:
            frames = list(map(int, group.split(",")))
            if frames != sorted(set(frames)) or not all(0 <= f < ep.n for f in frames):
                raise ValueError("frame groups must be ordered unique in-range indices")
            plans.append((ep.chunk_of_frame(frames[0]), ep.chunk_of_frame(frames[-1]), frames))
    if args.frame_stride is not None:
        if args.frame_stride < 1 or not 0 <= args.offset < args.frame_stride:
            raise ValueError("invalid single-frame sampling configuration")
        plans = [(ep.chunk_of_frame(f), ep.chunk_of_frame(f), [f])
                 for f in sorted(set(range(args.offset, ep.n, args.frame_stride)) | {ep.n - 1})]
    if args.refine_from:
        from combine_local_evidence import consensus_frames, transitions
        source = WIN_OUT / "segmentation_lab" / args.refine_from / args.dataset / f"ep{args.episode:04d}"
        proposed = transitions(consensus_frames([json.loads(f.read_text()) for f in source.glob("state_*.json")]))
        frames = sorted({f for event in proposed for f in range(max(0, event["last_before_frame"] - 2),
                                                               min(ep.n, event["first_after_frame"] + 3))})
        plans = [(ep.chunk_of_frame(f), ep.chunk_of_frame(f), [f]) for f in frames]
    backend = None
    rows = []
    for config in args.configs:
        kind, camera = config.split("_")
        for lo, hi, frames in plans:
            system, content = content_for(ep, frames, camera, kind)
            if args.scale != 1:
                for block in content:
                    if block["type"] == "image":
                        im = block["image"]
                        block["image"] = im.resize((int(im.width * args.scale), int(im.height * args.scale)), Image.Resampling.LANCZOS)
            digest = hashlib.sha256(system.encode())
            for b in content:
                digest.update(b["text"].encode() if b["type"] == "text" else b["image"].tobytes())
            input_hash = digest.hexdigest()
            for repeat in range(args.repeats):
                name = f"{config}_s{args.stride}_w{lo:02d}-{hi:02d}_t{args.temperature}_r{repeat}"
                if args.frame_groups or args.frame_stride is not None or args.refine_from:
                    name += "_frames" + "-".join(map(str, frames))
                if args.native:
                    name += "_native"
                if args.scale != 1:
                    name += f"_scale{args.scale}"
                path = root / f"{name}.json"
                if path.exists():
                    row = json.loads(path.read_text())
                    if row["input_hash"] != input_hash:
                        raise ValueError("input changed; use a new tag")
                else:
                    if backend is None:
                        from backend_qwen import QwenBackend
                        backend = QwenBackend("Qwen/Qwen3-VL-8B-Instruct")
                    import torch
                    torch.manual_seed(4200 + repeat)
                    if args.native:
                        inputs = backend._inputs(system, content)
                        start = time.time()
                        torch.cuda.reset_peak_memory_stats()
                        backend.model.model.rope_deltas = None
                        with torch.inference_mode():
                            output = backend.model.generate(**inputs, do_sample=args.temperature > 0,
                                **({"temperature": args.temperature, "top_p": 0.8, "top_k": 20} if args.temperature > 0 else {}),
                                max_new_tokens=2000, pad_token_id=backend.processor.tokenizer.pad_token_id)
                        raw = backend.processor.batch_decode(output[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]
                        backend.last = {"native": True, "gen_s": round(time.time() - start, 2),
                                        "max_mem_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2)}
                        del inputs, output
                    else:
                        raw = backend.generate(system, content, k=1, temperature=args.temperature, max_new_tokens=2000, batch=1)[0]
                    row = {"config": config, "window": [lo, hi], "frames": frames, "stride": args.stride,
                           "temperature": args.temperature, "repeat": repeat, "seed": 4200 + repeat,
                           "input_hash": input_hash, "system": system, "raw": raw, "generation": dict(backend.last)}
                    try:
                        row["parsed"] = parse_states(raw, frames) if kind == "state" else parse_events(raw, frames)
                    except Exception as exc:
                        row["error"] = str(exc)
                    dump_json(row, path)
                rows.append(row)
                print(f"{name}: {row.get('error') or row.get('parsed')}", flush=True)
                dump_json(score(ep, rows), root / "latest_scores.json")
    dump_json({"args": vars(args), "scores": score(ep, rows)}, root / "run_summary.json")
    print(f"LAB_OK {root}", flush=True)


if __name__ == "__main__":
    main()
