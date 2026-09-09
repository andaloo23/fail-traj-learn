"""Build a visual review of the combined segmentation and all saved ablation results."""
import argparse
import html
import json
from pathlib import Path
import subprocess

from common import WIN_OUT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tag", default="event_first_review")
    p.add_argument("--dataset", default="full_shift8__t0")
    p.add_argument("--episode", type=int, default=0)
    args = p.parse_args()
    base = WIN_OUT / "segmentation_lab"
    root = base / args.tag / args.dataset / f"ep{args.episode:04d}"
    result = json.loads((root / "result.json").read_text())
    # Reuse the already rendered camera strip; crop away every old p8 label/header.
    source = WIN_OUT / "annotation_review" / "qwen3vl8b_p8_smoke" / args.dataset / f"ep{args.episode:04d}" / "annotated.mp4"
    if source.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-vf", "crop=1104:512:0:144",
                        "-an", "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(root / "cameras.mp4")], check=True)
    configs = []
    query_count = response_count = 0
    for tag in sorted(base.iterdir()):
        folder = tag / args.dataset / f"ep{args.episode:04d}"
        files = list(folder.glob("state_*.json")) + list(folder.glob("events_*.json")) + list(folder.glob("video_*.json")) + list(folder.glob("chunk_*.json"))
        if not files:
            continue
        queries = len(files)
        responses = 0
        errors = 0
        for f in files:
            row = json.loads(f.read_text())
            samples = row.get("samples", [row])
            responses += len(samples)
            errors += sum("error" in s for s in samples)
        query_count += queries
        response_count += responses
        configs.append({"tag": tag.name, "queries": queries, "responses": responses, "invalid": errors})
    dump = {"queries": query_count, "responses": response_count, "runs": configs}
    (root / "trial_counts.json").write_text(json.dumps(dump, indent=2))
    colors = {"progress": "#46b98f", "failure_inducing": "#ed7373", "neutral": "#9ca7b7", "recovery": "#78b9f9", "uncertain": "#e5b952"}
    timeline = ''.join(f'<button title="Chunk {r["chunk"]}: {r["label"]}" style="background:{colors[r["label"]]}" onclick="v.currentTime={r["chunk"] / 2};v.play()">{r["chunk"]}</button>' for r in result["chunks"])
    rows = ''.join(f'<tr><td>{r["chunk"]}</td><td style="color:{colors[r["label"]]}">{r["label"]}</td><td>{r["local_label"]}</td><td>{r["context_label"]}</td><td>{html.escape(", ".join(r["notes"]))}</td></tr>' for r in result["chunks"])
    ablations = ''.join(f'<tr><td>{html.escape(r["tag"])}</td><td>{r["queries"]}</td><td>{r["responses"]}</td><td>{r["invalid"]}</td></tr>' for r in configs)
    page = '''<!doctype html><meta charset="utf-8"><title>Qwen segmentation iteration review</title>
<style>body{max-width:1200px;margin:28px auto;padding:0 16px;background:#111925;color:#e5edf8;font:17px system-ui}video{width:100%}table{border-collapse:collapse;width:100%}td,th{padding:8px;text-align:left;border-bottom:1px solid #344056}p{line-height:1.6}button,select{padding:8px;border:0;margin:2px;border-radius:4px;cursor:pointer}#timeline{display:flex}#timeline button{flex:1;padding:7px 0}a{color:#8edcff}#current{font-size:22px;padding:14px 0}</style>
<h1>Qwen segmentation: iteration results</h1>
<p>The useful change was independent enlarged frame judgments, followed by confirmed state transitions and a separate chunk-label pass.
The critical chunk-11 / chunk-12 distinction survives shifted sampling, changed context and repeated samples.
This is development on one reviewed episode, not evidence of generalization.</p>
<video id="v" controls src="cameras.mp4"></video><div id="current">Play to inspect the current chunk.</div>
<select onchange="v.playbackRate=Number(this.value)"><option value="1">Normal speed</option><option value="0.5">Half speed</option><option value="0.25">Quarter speed</option></select>
<div id="timeline">TIMELINE</div>
<p>Green: progress. Red: failure-inducing. Gray: neutral. Yellow: uncertain / review needed.
Uncertainty is intentional: early approach labels and some descriptions remain unreliable. No root-cause time or irrecoverability is inferred.</p>
<h2>State transitions</h2><pre>EVENTS</pre><p>These are Qwen-derived visual brackets, not simulator contact timestamps.</p>
<h2>Per-chunk comparison</h2><table><tr><th>Chunk</th><th>Reviewed candidate</th><th>Local pass</th><th>Changed context</th><th>Flags</th></tr>ROWS</table>
<h2>Saved ablations</h2><p>COUNTS</p><table><tr><th>Run</th><th>Queries</th><th>Responses</th><th>Invalid responses</th></tr>ABLATIONS</table>
<p><a href="result.json">Full combined evidence</a> | <a href="trial_counts.json">Trial counts</a></p>
<script>const data=DATA;const video=document.getElementById('v');video.addEventListener('timeupdate',()=>{const c=Math.min(data.length-1,Math.floor(video.currentTime*2));const r=data[c];document.getElementById('current').textContent=`${video.currentTime.toFixed(2)}s | chunk ${c} | ${r.label} | ${r.provenance}`;});</script>'''
    page = page.replace("TIMELINE", timeline).replace("EVENTS", html.escape(json.dumps(result["events"], indent=2))).replace("ROWS", rows)
    page = page.replace("COUNTS", f"{query_count} saved queries; {response_count} raw model responses. Counts include failed approaches, not independent validation examples.")
    page = page.replace("ABLATIONS", ablations).replace("DATA", json.dumps(result["chunks"]).replace("<", "\\u003c"))
    (root / "index.html").write_text(page)
    print(root / "index.html")


if __name__ == "__main__":
    main()
