"""Review videos for the observable-only sparse annotations: cameras at 2x, a per-FRAME bar with the sparse labels
(green progress, red failure_inducing, dark = unlabelled), the oracle chunk timeline below it for comparison, and a
text panel with the sparse event/reason at the current frame plus the oracle's view of the same frame.

Usage: render_sparse_review.py [--root outputs/observable_sparse_v1] [--ids E01 E02 ...]
Outputs: <root>/review/<id>/video.mp4 + poster.jpg, and <root>/review/index.html
"""
import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import review_oracle as ro  # noqa: E402
from common import WIN_OUT, Episode, open_dataset  # noqa: E402
from oracle_reference import ref_path  # noqa: E402

SPARSE_COLORS = {"progress": ro.LABEL_COLORS["progress"], "failure_inducing": ro.LABEL_COLORS["failure_inducing"]}
UNLABELLED = "#2a3140"


def load_sparse(root):
    per = defaultdict(dict)
    for r in csv.DictReader(open(root / "labelled_timesteps.csv", encoding="utf-8")):
        per[r["id"]][int(r["frame"])] = (r["label"], r["event"], r["reason"])
    return per


def draw_sparse_bar(d, labels, n, x0, x1, y, h, playhead):
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        xb = x0 + (x1 - x0) * (i + 1) / n
        lab = labels.get(i)
        d.rectangle((xa, y, xb, y + h), fill=SPARSE_COLORS.get(lab[0], UNLABELLED) if lab else UNLABELLED)
    xp = x0 + (x1 - x0) * (playhead + 0.5) / n
    d.line((xp, y - 4, xp, y + h + 4), fill="white", width=2)


def compose(ref, sparse, agent, wrist, i, L, fonts, eid, states, objects, fps):
    n = int(ref["n_frames"])
    c = ro.chunk_of(ref, i)
    cl = ref["chunk_labels"][c]
    im = Image.new("RGB", (L.width, L.height + 70), ro.BG)
    im.paste(Image.fromarray(agent).resize((L.cam, L.cam), Image.NEAREST), (L.cam_x, 0))
    im.paste(Image.fromarray(wrist).resize((L.cam, L.cam), Image.NEAREST), (L.cam_x + L.cam, 0))
    d = ImageDraw.Draw(im)
    tag = f"f {i:3d}  c {c:2d}"
    tw = d.textlength(tag, font=fonts["mono"])
    d.rectangle((L.cam_x + 6, 6, L.cam_x + 6 + tw + 12, 36), fill=(0, 0, 0))
    d.text((L.cam_x + 12, 9), tag, font=fonts["mono"], fill=ro.ACCENT)
    d.text((L.cam_x + L.cam + 12, 8), "wrist", font=fonts["small"], fill=ro.FG)
    d.text((L.cam_x + 12, L.cam - 28), "agentview", font=fonts["small"], fill=ro.FG)
    # bar 1: sparse observable labels per frame
    y1 = L.tl_top + 22
    d.text((L.tl_x0, y1 - 18), "observable-only sparse labels (per frame; dark = unlabelled)", font=fonts["small"], fill=ro.DIM)
    draw_sparse_bar(d, sparse, n, L.tl_x0, L.tl_x1, y1, 18, i)
    # bar 2: oracle chunk timeline (r4 reference) with its event markers
    y2 = y1 + 18 + 44
    d.text((L.tl_x0, y2 - 40), f"oracle {ref.get('reference_version')} chunk labels + events (withheld simulator state)", font=fonts["small"], fill=ro.DIM)
    ro.draw_timeline(im, ref, L.tl_x0, L.tl_x1, y2, L.tl_h, playhead=i, fonts=fonts)
    d = ImageDraw.Draw(im)
    # text panel
    y, lh = y2 + L.tl_h + 34, 24
    maxw = L.width - 2 * L.tl_x0
    outcome = "success" if ref.get("success") else "failure"
    d.text((L.tl_x0, y), f"{eid}  {ref['dataset']} / episode {ref['episode_index']}   outcome (withheld from annotator): {outcome}", font=fonts["title"], fill=ro.FG)
    y += lh + 6
    for line in ro.wrap_text(d, f"task: {ref['task']}", fonts["text"], maxw)[:2]:
        d.text((L.tl_x0, y), line, font=fonts["text"], fill=ro.FG)
        y += lh
    d.text((L.tl_x0, y), f"frame {i} / {n}   t = {i / fps:05.2f} s   chunk {c}", font=fonts["text"], fill=ro.FG)
    y += lh + 4
    lab = sparse.get(i)
    if lab:
        d.text((L.tl_x0, y), f"SPARSE: {lab[0].upper()}  ({lab[1]})", font=fonts["bold"], fill=SPARSE_COLORS[lab[0]])
        y += lh
        for line in ro.wrap_text(d, "reason: " + lab[2], fonts["small"], maxw)[:3]:
            d.text((L.tl_x0, y), line, font=fonts["small"], fill=ro.FG)
            y += lh - 6
    else:
        d.text((L.tl_x0, y), "SPARSE: unlabelled (annotator chose not to assert anything here)", font=fonts["bold"], fill=ro.DIM)
        y += lh
        y += 2 * (lh - 6)
    y += 6
    d.text((L.tl_x0, y), f"ORACLE: {cl['primary'].upper()}   allowed {{{', '.join(cl['allowed'])}}}   rule: {cl['rule']}", font=fonts["text"],
           fill=ro.LABEL_COLORS[cl["primary"]])
    y += lh
    s, o = states[i], objects[i]
    d.text((L.tl_x0, y), f"oracle held state: {s}   object: {o or '-'}   failure_mode: {ref['failure_mode']}   decisive: {ref.get('decisive_chunk')}",
           font=fonts["small"], fill="#8edbfb")
    y += lh - 2
    for line in ro.wrap_text(d, "oracle events: " + ro.events_text(ref), fonts["small"], maxw)[:3]:
        d.text((L.tl_x0, y), line, font=fonts["small"], fill=ro.DIM)
        y += lh - 6
    ro.draw_legend(d, L.tl_x0, im.height - 46, fonts)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(WIN_OUT / "observable_sparse_v1"))
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--fps", type=int, default=20)
    args = ap.parse_args()
    root = Path(args.root)
    manifest = {m["id"]: m for m in json.load(open(root / "private_manifest.json"))}
    sparse_all = load_sparse(root)
    out_root = root / "review"
    out_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for eid in (args.ids or sorted(manifest)):
        m = manifest[eid]
        t0 = time.time()
        ds = open_dataset(m["dataset"])
        ep = Episode(ds, m["dataset"], m["episode_index"])
        ref = json.load(open(ref_path(m["dataset"], m["episode_index"])))
        L, fonts = ro.Layout(2), ro.load_fonts()
        states, objects = ro.held_by_frame(ref)
        agent, wrist, how = ro.decode_episode(ds, ep)
        out_dir = out_root / eid
        out_dir.mkdir(parents=True, exist_ok=True)
        sparse = sparse_all.get(eid, {})
        first_lab = min(sparse) if sparse else ep.n // 2
        proc = ro.ffmpeg_pipe(out_dir / "video.mp4", L.width, L.height + 70, args.fps)
        try:
            for i in range(ep.n):
                im = compose(ref, sparse, agent[i], wrist[i], i, L, fonts, eid, states, objects, args.fps)
                if i == first_lab:
                    im.save(out_dir / "poster.jpg", quality=88)
                proc.stdin.write(im.tobytes())
        finally:
            proc.stdin.close()
            code = proc.wait()
        if code:
            raise RuntimeError(f"ffmpeg failed ({code}) for {eid}")
        segs = sorted({(lab[1], lab[0]) for lab in sparse.values()})
        rows.append((eid, m["dataset"], m["episode_index"], ref["failure_mode"], ref.get("reference_version"), len(sparse), ep.n, segs))
        print(f"RENDER_OK {eid} {m['dataset']} ep{m['episode_index']} {ep.n} frames, {len(sparse)} labelled, oracle {ref.get('reference_version')} [{time.time() - t0:.0f}s]", flush=True)
    html = ["<html><head><meta charset='utf-8'><title>Observable sparse labels vs oracle</title>",
            "<style>body{font-family:sans-serif;background:#111722;color:#e8edf5} video{width:100%;max-width:1024px} .ep{margin:24px 0;padding:12px;border:1px solid #333}</style></head><body>",
            "<h1>Observable-only sparse labels (top bar) vs oracle chunk labels (bottom bar)</h1>",
            "<p>Top bar: per-frame labels written from observable data only, dark where the annotator asserted nothing. "
            "Bottom bar: the simulator-derived reference (withheld from the annotator) with grasp/drop/release/attempt markers.</p>"]
    for eid, dsn, epi, mode, ver, nl, n, segs in rows:
        html.append(f"<div class='ep'><h2>{eid} &mdash; {dsn} ep {epi} &mdash; oracle mode {mode} ({ver})</h2>"
                    f"<p>{nl} of {n} frames labelled: {', '.join(f'{e} ({l})' for e, l in segs)}</p>"
                    f"<video controls preload='metadata' poster='{eid}/poster.jpg'><source src='{eid}/video.mp4' type='video/mp4'></video></div>")
    html.append("</body></html>")
    (out_root / "index.html").write_text("\n".join(html), encoding="utf-8")
    print(f"gallery: {out_root / 'index.html'}")


if __name__ == "__main__":
    main()
