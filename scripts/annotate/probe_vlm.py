"""Ask the VLM free-form questions about specific chunk tiles, to diagnose perception vs reasoning problems.
Usage: probe_vlm.py <dataset> <episode> --chunks 8 10 12 [--scale 1 2] [--question "..."] [--wrist-only]
Each (scale) prints the model's answer for the listed tiles shown together."""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend_qwen import QwenBackend  # noqa: E402
from common import Episode, open_dataset  # noqa: E402
from render import tile_frame  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("dataset")
ap.add_argument("episode", type=int)
ap.add_argument("--chunks", nargs="+", type=int, required=True)
ap.add_argument("--scale", nargs="+", type=float, default=[1.0])
ap.add_argument("--wrist-only", action="store_true")
ap.add_argument("--question", default="For each image: what object is the gripper holding or about to grasp, if any? Describe its shape, "
                "colours and label text. Then list every other object you can see on the table with its colours.")
ap.add_argument("--model", default="Qwen/Qwen3-VL-8B-Instruct")
args = ap.parse_args()

ds = open_dataset(args.dataset)
ep = Episode(ds, args.dataset, args.episode)
print(f"task: {ep.task}\nobjects: {ep.meta['object_slots']} targets: {ep.meta['target_objects']}")
backend = QwenBackend(args.model)
for scale in args.scale:
    content = [{"type": "text", "text": f"Instruction given to the robot: \"{ep.task}\". Images from the episode:"}]
    for c in args.chunks:
        a, b = ep.chunks[c]
        i = (a + b) // 2
        ag, wr = ep.frame(i)
        img = Image.fromarray(wr) if args.wrist_only else tile_frame(ag, wr, f"chunk {c}")
        if scale != 1.0:
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        content.append({"type": "text", "text": f"chunk {c} (step {i}):"})
        content.append({"type": "image", "image": img})
    content.append({"type": "text", "text": args.question})
    outs = backend.generate("You are a careful visual inspector. Answer concretely.", content, k=1, temperature=0.0, max_new_tokens=400, batch=1)
    print(f"\n=== scale {scale} (tile {img.size}, {backend.last['input_tokens']} tokens, {backend.last['gen_s']}s)\n{outs[0]}")
