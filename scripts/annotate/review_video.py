"""Render an annotation audit video and local HTML player without invoking a VLM.

Usage: review_video.py TAG DATASET EPISODE [--review-chunk N]
The optional review marker is a prior human hypothesis, not verified ground truth.
"""
import argparse
import html
import json
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from aggregate import quality_flags
from common import Episode, WIN_OUT, annot_path, open_dataset


COLORS = {"progress": "#4ac698", "failure_inducing": "#ff7878", "recovery": "#71afff",
          "neutral": "#a3aabd", "aftermath": "#c69bdf"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("dataset")
    parser.add_argument("episode", type=int)
    parser.add_argument("--review-chunk", type=int)
    args = parser.parse_args()
    record = json.loads(annot_path(args.tag, args.dataset, args.episode).read_text())
    ann = record["annotation"]
    ep = Episode(open_dataset(args.dataset), args.dataset, args.episode)
    out = WIN_OUT / "annotation_review" / args.tag / args.dataset / f"ep{args.episode:04d}"
    out.mkdir(parents=True, exist_ok=True)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 22)
    small = ImageFont.truetype(font_path, 18)
    title = ImageFont.truetype(font_path, 27)
    target = int(np.flatnonzero(ep.col("priv.target_mask")[0])[0])
    slots = ep.meta["object_slots"]
    grasps = ep.col("priv.obj_grasped")
    contact = ep.col("priv.obj_gripper_contact")[:, target]
    support = ep.col("priv.obj_resting")[:, target]
    positions = ep.col("priv.obj_pos").reshape(ep.n, -1, 3)
    decisive = ann["landmarks"]["decisive_error"]["value"]
    coarse = ann.get("landmarks_coarse", ann["landmarks"])["decisive_error"]["value"]
    flags = quality_flags(ann)
    width, height = 1104, 940
    output = out / "annotated.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{width}x{height}", "-r", str(ep.fps), "-i", "-", "-an", "-c:v", "libx264",
           "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(ep.n):
            c = ep.chunk_of_frame(i)
            im = Image.new("RGB", (width, height), "#111722")
            d = ImageDraw.Draw(im)
            d.text((24, 15), "P8 annotation audit | prediction is NOT ground truth", font=title, fill="white")
            d.text((24, 54), ep.task, font=small, fill="#d8dfea")
            d.text((24, 83), f"{args.dataset} / episode {args.episode} | recorded outcome: failure | {i / ep.fps:05.2f}s / {ep.n / ep.fps:.1f}s | frame {i} | chunk {c}", font=small, fill="#d8dfea")
            d.text((24, 117), "AGENT CAMERA", font=small, fill="#d8dfea")
            d.text((568, 117), "WRIST CAMERA", font=small, fill="#d8dfea")
            agent, wrist = ep.frame(i)
            im.paste(Image.fromarray(agent).resize((512, 512)), (24, 144))
            im.paste(Image.fromarray(wrist).resize((512, 512)), (568, 144))
            label = ann["chunk_label"][c]
            d.text((24, 671), f"VLM label: {label}  |  vote support: {ann['chunk_q'][c]:.0%} (uncalibrated)", font=font, fill=COLORS[label])
            held = ", ".join(slots[j] for j in range(min(len(slots), grasps.shape[1])) if grasps[i, j]) or "none"
            d.text((24, 707), f"Simulator finger-contact grasp flag: {held}", font=small, fill="#8edbfb")
            d.text((24, 735), f"Target: {slots[target]} | contact={int(contact[i])} resting={int(support[i])} height={positions[i, target, 2]:.3f}m", font=small, fill="#8edbfb")
            d.text((24, 769), f"Predicted decisive error: chunk {decisive} (coarse {coarse}) | episode cause: {ann['cause']}", font=small, fill="#ffb6b6")
            if args.review_chunk is not None:
                d.text((24, 797), f"Prior review hypothesis: slip near chunk {args.review_chunk}. Check the video and simulator signals.", font=small, fill="#ffd56b")
            left, right, y = 24, 1080, 857
            for chunk, (a, b) in enumerate(ep.chunks):
                x0, x1 = left + a / ep.n * (right - left), left + b / ep.n * (right - left)
                d.rectangle((x0, y, x1, y + 23), fill=COLORS[ann["chunk_label"][chunk]])
            for marker, color, name in [(decisive, "#ff7777", "VLM"), (args.review_chunk, "#ffd56b", "review")]:
                if marker is not None and 0 <= marker < ep.n_chunks:
                    x = left + ep.chunks[marker][0] / ep.n * (right - left)
                    d.line((x, y - 21, x, y + 26), fill=color, width=3)
                    d.text((x + 4, y - 25), name, font=small, fill=color)
            x = left + i / ep.n * (right - left)
            d.line((x, y - 3, x, y + 30), fill="white", width=3)
            d.text((24, 900), "REVIEW REQUIRED: " + (", ".join(flags) or "semantic accuracy unverified"), font=small, fill="#ffd56b")
            if i == ep.chunks[args.review_chunk if args.review_chunk is not None else 0][0]:
                im.save(out / "poster.jpg")
            process.stdin.write(im.tobytes())
    finally:
        process.stdin.close()
        code = process.wait()
    if code:
        raise RuntimeError(f"ffmpeg failed with exit code {code}")
    bookmarks = [("Start", 0)]
    for name, chunk in [("Predicted error", decisive), ("Coarse error", coarse), ("Prior review: inspect slip", args.review_chunk)]:
        if chunk is not None:
            bookmarks.append((f"{name} (chunk {chunk})", max(0, ep.chunks[chunk][0] / ep.fps - 0.5)))
    buttons = " ".join(f'<button onclick="v.currentTime={t};v.play()">{html.escape(name)}</button>' for name, t in bookmarks)
    page = f'''<!doctype html><meta charset="utf-8"><title>P8 annotation review</title>
<style>body{{background:#111722;color:#e8edf5;font:17px system-ui;max-width:1104px;margin:24px auto;padding:0 16px}}video{{width:100%;max-height:75vh}}button,select{{padding:9px;margin:4px;background:#263449;color:white;border:1px solid #51627a;border-radius:6px}}p{{line-height:1.6}}code{{color:#ffd56b}}</style>
<h1>P8 smoke test: inspect the annotation</h1><p>{html.escape(ep.task)}</p>
<video id="v" controls preload="metadata" poster="poster.jpg" src="annotated.mp4"></video>
<div>{buttons} <select onchange="v.playbackRate=Number(this.value)"><option value="1">Normal speed</option><option value="0.5">Half speed</option><option value="0.25">Quarter speed</option></select></div>
<p><b>How to verify:</b> Watch the cameras first. Identify the object picked up, when it leaves the gripper,
and whether the robot makes another meaningful attempt. Compare those events with the colored labels.
Blue text reports simulator signals, which were not shown to the VLM. Contact flags are evidence, not causal ground truth.</p>
<p><b>Known issue:</b> the refined error is at chunk {decisive}, while the prior review places a slip near chunk {args.review_chunk}.
The episode is masked from annotation training because its decisive error falls outside its failure-inducing segments.
100% vote support means agreement, not verified correctness. Chunk indices start at zero; each chunk is about 0.5 seconds.</p>
<p><b>Model narrative (unverified):</b> {html.escape(ann.get('failure_symptom') or '')}</p>
<p><a href="annotation.json" style="color:#8edbfb">Full annotation JSON</a></p>'''
    (out / "index.html").write_text(page)
    (out / "annotation.json").write_text(json.dumps(record, indent=2))
    print(f"VIDEO_OK {ep.n} frames, {ep.n / ep.fps:.1f}s: {output}")


if __name__ == "__main__":
    main()
