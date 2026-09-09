"""Native-video Qwen comparison, using temporal video tokens rather than independent image tokens."""
import argparse
import json
import time

import numpy as np
from PIL import Image
import torch

from backend_qwen import QwenBackend
from common import Episode, WIN_OUT, dump_json, open_dataset
from prompt import scene_glossary
from schema import extract_json


SYSTEM = """Describe the visible robot behavior over time in this video. Agent view is left, wrist view right.
The white mechanical housing is part of the robot, not a grasped mug. Distinguish approach, grasp, carrying,
loss/release and motion without an object. Do not invent causes or infer that recovery is impossible.
Return JSON: {"observation":"what visibly happens", "segments":[{"start_s":0.0,"end_s":0.0,
"label":"progress|failure_inducing|recovery|neutral|uncertain","evidence":"visible evidence"}],
"loss_times_s":[]}. Use actual displayed video times; the numeric schema placeholders are not event times.
Progress includes approaching the correct object as well as carrying it. Label a visible harmful loss in
its own interval, not the earlier stable carry. Neutral includes idle or empty motion without task progress.
Use uncertain where evidence is insufficient. loss_times_s lists visible detachments, not root-cause times.
"""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--windows", nargs="+", default=["0:3", "8:11", "10:13", "12:15", "0:27"])
    p.add_argument("--tag", default="lab_v7_video")
    p.add_argument("--dataset", default="full_shift8__t0")
    p.add_argument("--episode", type=int, default=0)
    args = p.parse_args()
    ep = Episode(open_dataset(args.dataset), args.dataset, args.episode)
    backend = QwenBackend("Qwen/Qwen3-VL-8B-Instruct")
    root = WIN_OUT / "segmentation_lab" / args.tag / args.dataset / f"ep{args.episode:04d}"
    for window in args.windows:
        lo, hi = map(int, window.split(":"))
        path = root / f"video_{lo:02d}_{hi:02d}.json"
        if path.exists():
            print(f"skip {window}", flush=True)
            continue
        stride = 5 if hi - lo > 8 else 2
        indices = sorted(set(range(ep.chunks[lo][0], ep.chunks[hi][1], stride)) | {ep.chunks[hi][1] - 1})
        frames = []
        for i in indices:
            ag, wr = ep.frame(i)
            frames.append(np.asarray(Image.fromarray(np.concatenate([ag, wr], axis=1)).resize((1024, 512), Image.Resampling.LANCZOS)))
        text = f"Task: {ep.task}\n{scene_glossary(ep.meta['object_slots'])}\nVideo timestamps are absolute episode seconds. Describe this excerpt only."
        messages = [{"role": "system", "content": [{"type": "text", "text": SYSTEM}]},
                    {"role": "user", "content": [{"type": "text", "text": text}, {"type": "video"}]}]
        chat = backend.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = backend.processor(text=[chat], videos=[np.stack(frames)],
            video_metadata=[{"total_num_frames": ep.n, "fps": ep.fps, "frames_indices": indices}],
            do_sample_frames=False, do_resize=False, return_tensors="pt").to(backend.device)
        backend.model.model.rope_deltas = None
        torch.cuda.reset_peak_memory_stats()
        start = time.time()
        with torch.inference_mode():
            output = backend.model.generate(**inputs, do_sample=False, max_new_tokens=1500,
                                           pad_token_id=backend.processor.tokenizer.pad_token_id)
        raw = backend.processor.batch_decode(output[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]
        row = {"system": SYSTEM, "input_text": text, "frames": indices, "window": [lo, hi], "raw": raw,
               "input_tokens": inputs["input_ids"].shape[1], "seconds": time.time() - start,
               "peak_gib": torch.cuda.max_memory_allocated() / 2**30}
        try:
            row["parsed"] = json.loads(extract_json(raw))
        except Exception as exc:
            row["error"] = str(exc)
        dump_json(row, path)
        print(f"VIDEO {window}: {raw}", flush=True)
        del inputs, output
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
