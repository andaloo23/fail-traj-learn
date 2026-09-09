"""Experimental chunk-local segmentation, with independent judgments and no episode-outcome prompt.

Uses recorded images, task/glossary and commanded gripper action only. No oracle/reference is loaded.
"""
import argparse
from collections import Counter
import hashlib
import json

from PIL import Image
import numpy as np

from common import Episode, WIN_OUT, dump_json, open_dataset
from prompt import scene_glossary
from schema import extract_json


SYSTEM = """Review only the explicitly named TARGET action chunk in this robot video excerpt.
The task and object appearance glossary describe intended behavior, not what actually happened.
Camera observations may include context before and after the target chunk. Do not assign events in that
context to the target chunk. Each image pair is external camera left, wrist camera right.
The robot's white housing/fingers are not a grasped white mug. Check the actual external object's motion.
First describe the visible action during the target chunk. Then choose one label:
progress: approaches the correct target, grasps, lifts, transports or places it in accordance with the task.
failure_inducing: visible wrong-object interaction, harmful collision, loss/drop, or incorrect placement
occurs during this chunk. Do not label a stable carry as a bad grasp based on a later drop.
recovery: visible corrective action in response to an error already visible in the supplied excerpt.
neutral: no meaningful visible task change, including waiting or small movements of an empty gripper.
uncertain: observations do not support a choice.
Do not infer irrecoverability, causal root errors, or episode outcome. Describe object identity as uncertain
when ambiguous. A loss while commanded closed is a candidate slip; the command alone does not prove holding.
Event timing is handled by a separate visual tracker. Do not invent frame indices in this judgment.
The observation at frame b is AFTER actions a through b-1. Thus a change from b-1 to b belongs to the target
chunk ending at b-1. Never penalize an earlier chunk merely because the later context contains a loss.
Return JSON only:
{"label":"progress|failure_inducing|recovery|neutral|uncertain", "object":"name or null",
 "observation":"brief visible evidence", "event":"none|approach|grasp|lift|transport|loss|release|collision|wrong_object|placement|other"}
"""


def validate(raw, frames):
    d = json.loads(extract_json(raw))
    aliases = {"drop": "loss", "slip": "loss", "holding": "other", "hold": "other", "reach": "approach"}
    if d.get("event") in aliases:
        d["event_original"] = d["event"]
        d["event"] = aliases[d["event"]]
    if d.get("label") not in ("progress", "failure_inducing", "recovery", "neutral", "uncertain"):
        raise ValueError("invalid label")
    if d.get("event") not in ("none", "approach", "grasp", "lift", "transport", "loss", "release", "collision", "wrong_object", "placement", "other"):
        raise ValueError("invalid event")
    a, b = d.get("last_before_frame"), d.get("first_after_frame")
    if any(v is not None and (type(v) is not int or v not in frames) for v in (a, b)):
        raise ValueError("event endpoints must be shown frames")
    if a is not None and b is not None and a >= b:
        raise ValueError("reversed event bracket")
    return d


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", default="full_shift8__t0")
    p.add_argument("--episode", type=int, default=0)
    p.add_argument("--tag", default="local_v1")
    p.add_argument("--chunks", nargs="+", type=int)
    p.add_argument("--context", type=int, default=0, help="Additional context frames before/after the chunk")
    p.add_argument("--scale", type=float, default=2)
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--temperature", type=float, default=0.3)
    p.add_argument("--seed", type=int, default=7100)
    p.add_argument("--motion", action="store_true", help="Supply measured proprioceptive displacement, never privileged object motion")
    p.add_argument("--states-tag", help="Supply tentative events from independent Qwen frame tracking")
    args = p.parse_args()
    ep = Episode(open_dataset(args.dataset), args.dataset, args.episode)
    root = WIN_OUT / "segmentation_lab" / args.tag / args.dataset / f"ep{args.episode:04d}"
    chosen = args.chunks if args.chunks is not None else list(range(ep.n_chunks))
    tracked_events = []
    if args.states_tag:
        from combine_local_evidence import consensus_frames, transitions
        source = WIN_OUT / "segmentation_lab" / args.states_tag / args.dataset / f"ep{args.episode:04d}"
        tracked_events = transitions(consensus_frames([json.loads(f.read_text()) for f in source.glob("state_*.json")]))
    backend = None
    records = []
    for c in chosen:
        a, b = ep.chunks[c]
        frames = sorted({max(0, a - args.context), a, (a + b) // 2, b - 1,
                         min(ep.n - 1, b), min(ep.n - 1, b + args.context)})
        task = f"Task: {ep.task}\nObject appearances:\n" + scene_glossary(ep.meta["object_slots"])
        command = ep.gripper_cmd[a:b]
        text = (task + f"\nTARGET chunk {c}: actions at frames {a} through {b - 1}.\n"
                f"Gripper command range in chunk: {command.min():.2f} to {command.max():.2f}; +1 close, -1 open.\n"
                "Judge only this target interval. Context images do not change its boundaries.")
        if args.motion:
            delta = (ep.eef_xyz[min(b, ep.n - 1)] - ep.eef_xyz[a]) * 100
            distance = float(np.linalg.norm(np.diff(ep.eef_xyz[a:min(b + 1, ep.n)], axis=0), axis=1).sum() * 100)
            text += (f"\nMeasured robot motion in the TARGET interval: xyz displacement in cm = {delta.round(2).tolist()}; "
                     f"end-effector path length = {distance:.2f} cm. This measures motion, not whether it is task-progressing. "
                     "Describe this motion consistently with the images; do not call substantial motion stationary.")
        if args.states_tag:
            recent = [e for e in tracked_events if e["first_after_frame"] <= a]
            current = [e for e in tracked_events if e["last_before_frame"] < b and e["first_after_frame"] > a]
            estimate = ("held" if recent[-1]["event"] == "grasp" else "empty") if recent else "not established"
            text += (f"\nSeparate visual tracker estimate at interval start: {estimate}. "
                     f"Its supported changes overlapping this interval: {json.dumps(current)}. "
                     "These are fallible Qwen visual estimates, not simulator facts. They required consecutive frame confirmations; "
                     "a loss_or_release is an observed transition, not a claim about root cause. Reconcile with these images.")
        content = [{"type": "text", "text": text}]
        digest = hashlib.sha256((SYSTEM + text + str((args.k, args.temperature, args.seed))).encode())
        for i in frames:
            ag, wr = ep.frame(i)
            im = Image.fromarray(np.concatenate([ag, wr], axis=1))
            im = im.resize((int(im.width * args.scale), int(im.height * args.scale)), Image.Resampling.LANCZOS)
            caption = f"Observation frame {i} ({i / ep.fps:.2f}s)"
            content.extend([{"type": "text", "text": caption}, {"type": "image", "image": im}])
            digest.update(caption.encode()); digest.update(im.tobytes())
        path = root / f"chunk_{c:03d}.json"
        if path.exists():
            row = json.loads(path.read_text())
            if row["input_hash"] != digest.hexdigest():
                raise ValueError("configuration changed; use a new tag")
        else:
            if backend is None:
                from backend_qwen import QwenBackend
                backend = QwenBackend("Qwen/Qwen3-VL-8B-Instruct")
            import torch
            torch.manual_seed(args.seed + c)
            raw = backend.generate(SYSTEM, content, k=args.k, temperature=args.temperature, max_new_tokens=420, batch=args.k)
            row = {"chunk": c, "frame_interval": [a, b], "frames": frames, "input_hash": digest.hexdigest(),
                   "system": SYSTEM, "input_text": text, "settings": vars(args), "generation": dict(backend.last), "samples": []}
            for response in raw:
                sample = {"raw": response}
                try:
                    sample["parsed"] = validate(response, frames)
                except Exception as exc:
                    sample["error"] = str(exc)
                row["samples"].append(sample)
            votes = Counter(s["parsed"]["label"] for s in row["samples"] if "parsed" in s)
            label, count = votes.most_common(1)[0] if votes else ("uncertain", 0)
            row["label"] = label if count * 2 > args.k else "uncertain"
            row["votes"] = dict(votes)
            row["support"] = count / args.k
            dump_json(row, path)
        records.append(row)
        print(f"chunk {c}: {row['label']} {row['votes']} | {[s.get('parsed', {}).get('observation') for s in row['samples']]}", flush=True)
    dump_json({"records": records, "warning": "Experimental visual segmentation; vote support is not calibrated accuracy."}, root / "segmentation.json")
    print(f"SEGMENT_OK {root}", flush=True)


if __name__ == "__main__":
    main()
