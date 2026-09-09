"""Export/render explicitly authored judgments. This script never infers labels.

Run with the repository Python environment (Pillow, numpy, ffmpeg required):
  python scripts/annotate/bench/render_direct_annotations.py [--skip-video]
"""
import argparse
import csv
import hashlib
import html
import json
import subprocess
import textwrap
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/gpt6_annotations_v1"
AUDIT = ROOT / "outputs/oracle_audit_r6"
COLORS = dict(progress="#58c998", failure_inducing="#f47f79", recovery="#74b9ff",
              neutral="#a8b0bd", aftermath="#d4a56b", uncertain="#c6a0ef")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def expand(authored, evidence):
    chunks = evidence["chunks"]
    rows = []
    for first, last, label, confidence, phase, reason in authored["segments"]:
        assert first == len(rows) and first <= last < len(chunks), "Gap/overlap in authored ranges"
        assert label in COLORS and confidence in {"high", "medium"} and reason
        for c in range(first, last + 1):
            a, b = chunks[c]
            rows.append(dict(chunk=c, start_frame=a, end_frame_exclusive=b,
                             label=label, confidence=confidence, phase=phase, reason=reason,
                             abstain=label == "uncertain", training_approved=False,
                             counterfactual_advantage=None))
    assert len(rows) == len(chunks)
    assert chunks[0][0] == 0 and chunks[-1][1] == evidence["n_frames"]
    assert all(a < b and (c == 0 or a == chunks[c - 1][1]) for c, (a, b) in enumerate(chunks))
    for attempt in authored["attempts"]:
        a, b = attempt["frames"]
        assert 0 <= a <= b < evidence["n_frames"]
    return rows


def font(size):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_video(directory, source, annotation):
    with np.load(source / "cameras.npz") as cameras:
        agent, wrist = cameras["agent"], cameras["wrist"]
    assert len(agent) == len(wrist) == annotation["n_frames"]
    width, height = 1024, 748
    small, title = font(17), font(22)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{width}x{height}", "-r", str(annotation["fps"]), "-i", "-",
                             "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(directory / "gpt6_direct_v1.mp4")],
                            stdin=subprocess.PIPE)
    try:
        for row in annotation["chunk_labels"]:
            base = Image.new("RGB", (width, height), "#101722")
            draw = ImageDraw.Draw(base)
            draw.text((16, 8), "GPT-6 direct v1 | candidate annotations", font=title, fill="white")
            draw.text((16, 38), f'{annotation["dataset"]} / ep{annotation["episode_index"]:04d}', font=small, fill="white")
            for k, line in enumerate(textwrap.wrap(annotation["task"], 105)):
                draw.text((16, 62 + k * 20), line, font=small, fill="#c8d2df")
            draw.text((16, 607), f'chunk {row["chunk"]} | {row["label"]} | {row["confidence"]} confidence',
                      font=title, fill=COLORS[row["label"]])
            for k, line in enumerate(textwrap.wrap(row["reason"], 108)):
                draw.text((16, 638 + k * 21), line, font=small, fill="white")
            for other in annotation["chunk_labels"]:
                a = 16 + 992 * other["start_frame"] / len(agent)
                b = 16 + 992 * other["end_frame_exclusive"] / len(agent)
                draw.rectangle((a, 715, b, 734), fill=COLORS[other["label"]])
            for frame in range(row["start_frame"], row["end_frame_exclusive"]):
                canvas = base.copy()
                pair = Image.fromarray(np.concatenate((agent[frame], wrist[frame]), axis=1)).resize((1024, 512))
                canvas.paste(pair, (0, 91))
                overlay = ImageDraw.Draw(canvas)
                overlay.rectangle((830, 91, 1024, 117), fill="#101722")
                overlay.text((842, 94), f'frame {frame}/{len(agent)-1}', font=small, fill="white")
                x = 16 + 992 * frame / len(agent)
                overlay.line((x, 710, x, 739), fill="white", width=3)
                if frame == min(54, len(agent) - 1):
                    canvas.save(directory / "poster.jpg", quality=92)
                proc.stdin.write(canvas.tobytes())
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code:
        raise RuntimeError(f"ffmpeg failed: {code}")


def build_page(annotations, stats):
    escape = html.escape
    pieces = ['''<!doctype html><html lang="en"><meta charset="utf-8">
<title>GPT-6 direct annotations v1</title><meta name="viewport" content="width=device-width">
<style>body{font:16px system-ui;background:#101722;color:#e5edf5;max-width:1100px;margin:32px auto;padding:0 20px}
a{color:#92caff}article{background:#1a2534;padding:22px;margin:24px 0;border-radius:12px}video{width:100%;max-width:1024px}
.timeline{display:flex;gap:2px;margin:16px 0}.timeline button{border:0;min-width:0;padding:10px 0;flex:1;cursor:pointer}
td,th{text-align:left;padding:8px;vertical-align:top;border-bottom:1px solid #354151}table{border-collapse:collapse;width:100%}
button{cursor:pointer} .current{outline:3px solid white}.legend span{display:inline-block;margin:5px 15px 5px 0}
.live{min-height:55px}small{color:#b7c7d7}</style>
<h1>GPT-6 direct annotations · v1</h1>
<p>Direct assistant judgments from paired-camera stills and simulator telemetry. This is a nonblind trial on the previous r6 audit sample, not human ground truth or a measured accuracy result.</p>
<p>Click a timeline chunk or segment start to seek. Purple means uncertain and abstains. Confidence is qualitative. Labels describe observed behavior; they do not establish counterfactual advantage or guarantee a successful spliced trajectory.</p>
<p><a href="README.md">Protocol</a> · <a href="authored.json">Authored judgments</a> · <a href="chunks.csv">All chunks CSV</a> · <a href="summary.json">Counts and r6 comparison</a></p>''']
    pieces.append(f'<p>{stats["episodes"]} episodes · {stats["chunks"]} chunks · {stats["label_counts"].get("uncertain", 0)} uncertain chunks. Production labels unchanged.</p>')
    pieces.append('<div class="legend">' + ''.join(f'<span style="color:{c}">{l}</span>' for l, c in COLORS.items()) + '</div>')
    for j, ann in enumerate(annotations):
        rel = f'{ann["dataset"]}/ep{ann["episode_index"]:04d}'
        pieces.append(f'<article id="episode{j}"><h2>{escape(rel)}</h2><p>{escape(ann["task"])}</p><p>{escape(ann["summary"])}</p>')
        pieces.append(f'<video id="v{j}" controls preload="none" poster="{rel}/poster.jpg" src="{rel}/gpt6_direct_v1.mp4"></video>')
        pieces.append(f'<div class="timeline" id="t{j}">')
        for row in ann["chunk_labels"]:
            title_text = escape(f'c{row["chunk"]}: {row["label"]} — {row["reason"]}', quote=True)
            pieces.append(f'<button title="{title_text}" aria-label="{title_text}" style="background:{COLORS[row["label"]]}" onclick="seek({j},{row["start_frame"]})">{row["chunk"]}</button>')
        pieces.append(f'</div><p class="live" id="l{j}"></p><p><a href="{rel}/gpt6_direct_v1.mp4">Video</a> · <a href="{rel}/annotation.json">Annotation JSON</a> · <a href="{rel}/evidence.json">Telemetry summary</a></p><details><summary>Segment reasons and attempt outcomes</summary><table><tr><th>Chunks</th><th>Judgment</th><th>Reason</th></tr>')
        for first, last, label, confidence, phase, reason in ann["segments"]:
            frame = ann["chunk_labels"][first]["start_frame"]
            pieces.append(f'<tr><td><button onclick="seek({j},{frame})">{first}–{last}</button></td><td style="color:{COLORS[label]}">{label}<br><small>{confidence}</small></td><td>{escape(reason)}</td></tr>')
        pieces.append('</table><ul>')
        for attempt in ann["attempts"]:
            pieces.append(f'<li>Frames {attempt["frames"]}: {escape(attempt["outcome"])} — {escape(attempt["reason"])}</li>')
        pieces.append('</ul></details></article>')
    payload = json.dumps([dict(fps=a["fps"], rows=a["chunk_labels"]) for a in annotations]).replace('<', '\\u003c')
    pieces.append('''<script>const data = ''' + payload + ''';
function seek(j,f){const v=document.getElementById('v'+j);v.currentTime=f/data[j].fps;update(j)}
function update(j){const v=document.getElementById('v'+j),d=data[j];const f=Math.min(d.rows.at(-1).end_frame_exclusive-1,Math.floor(v.currentTime*d.fps));
const r=d.rows.find(r=>r.start_frame<=f&&f<r.end_frame_exclusive);if(!r)return;
document.getElementById('l'+j).textContent=`Chunk ${r.chunk} · ${r.label} · ${r.confidence} confidence — ${r.reason}`;
document.querySelectorAll('#t'+j+' button').forEach((b,i)=>b.classList.toggle('current',i===r.chunk))}
data.forEach((_,j)=>{document.getElementById('v'+j).addEventListener('timeupdate',()=>update(j));update(j)});
</script></html>''')
    (OUT / "index.html").write_text('\n'.join(pieces), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-video", action="store_true")
    args = parser.parse_args()
    authored_bytes = (OUT / "authored.json").read_bytes()
    source_hash = hashlib.sha256(authored_bytes).hexdigest()
    authored = json.loads(authored_bytes)
    sample = json.loads((OUT / "sample.json").read_text())
    assert [(a["dataset"], a["episode_index"]) for a in authored["episodes"]] == [(a["dataset"], a["episode_index"]) for a in sample]
    annotations, csv_rows, comparisons = [], [], []
    for entry in authored["episodes"]:
        rel = Path(entry["dataset"]) / f'ep{entry["episode_index"]:04d}'
        directory, source = OUT / rel, AUDIT / rel
        evidence = json.loads((directory / "evidence.json").read_text())
        rows = expand(entry, evidence)
        ann = {**entry, **{k: evidence[k] for k in ("task", "success", "n_frames", "fps")},
               "version": "gpt6_direct_v1", "authored_sha256": source_hash,
               "provenance": "Direct assistant visual/telemetry judgments; nonblind reannotation of r6 audit sample",
               "human_validated": False, "decisive_error_frame": None, "recoverable_until_frame": None,
               "attempt_frame_bounds": "inclusive", "chunk_labels": rows}
        write_json(directory / "annotation.json", ann)
        # Comparison occurs only after reading the independently authored labels.
        reference = json.loads((source / "reference.json").read_text())
        assert reference["chunks"] == evidence["chunks"]
        for row, old in zip(rows, reference["chunk_labels"], strict=True):
            csv_rows.append(dict(dataset=entry["dataset"], episode_index=entry["episode_index"], **row))
            comparisons.append(dict(dataset=entry["dataset"], episode_index=entry["episode_index"], chunk=row["chunk"],
                                    direct=row["label"], r6_primary=old["primary"], r6_allowed=old["allowed"]))
        if not args.skip_video:
            render_video(directory, source, ann)
        annotations.append(ann)
        print(f'{rel}: {len(rows)} chunks exported', flush=True)
    with (OUT / "chunks.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    stats = dict(version="gpt6_direct_v1", authored_sha256=source_hash, episodes=len(annotations),
                 chunks=len(csv_rows), frames=sum(a["n_frames"] for a in annotations),
                 label_counts=dict(Counter(r["label"] for r in csv_rows)),
                 confidence_counts=dict(Counter(r["confidence"] for r in csv_rows)),
                 r6_primary_disagreements=sum(c["direct"] != c["r6_primary"] for c in comparisons),
                 comparison_note="Descriptive disagreement, not accuracy; semantics differ and trial was not blind.",
                 human_validated=False, production_modified=False)
    write_json(OUT / "summary.json", stats)
    write_json(OUT / "comparison_r6.json", comparisons)
    build_page(annotations, stats)
    print(json.dumps(stats), flush=True)


if __name__ == "__main__":
    main()
