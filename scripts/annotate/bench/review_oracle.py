"""Human review kit for the oracle segment annotations (docs/oracle_segmentation.md, "still to build" item 3).

  review_oracle.py --set heldout|dev|all|none [--extra dataset:ep ...] [--successes N] [--fps 20] [--scale 2]
                   [--overwrite] [--index-only] [--verify K]

For every selected episode the reference JSON under $FTL_BENCH/references (oracle_reference.py, r2) is rendered as a
real-time video (fps = recorder fps, so a 280-step episode lasts 14 s) under WIN_OUT/oracle_review/<dataset>/ep<NNNN>/:
  video.mp4       agentview | wrist at --scale, a chunk timeline coloured by primary label (hatched + lighter when the
                  allowed set has several labels), event markers (grasp up-triangle, drop red down-triangle, release blue
                  down-triangle), a bold marker at the decisive chunk, a moving playhead and a text panel with the
                  reference facts for the current frame; chunk index and frame number are burnt into the camera corner
  poster.jpg      the composed frame at the start of the decisive chunk (or the middle frame)
  reference.json  a copy of the reference
  review.json     the row used by the gallery and the audit sheet
  index.html      per-episode detail page (video + events + full chunk table)
plus, at WIN_OUT/oracle_review/: index.html (gallery with failure_mode / set filters, inline players and collapsible
chunk tables), audit_sheet.csv (oracle columns pre-filled, human columns empty) and audit_protocol.md.

Sets: heldout = bench/episodes.json (50), dev = bench/episodes_dev.json (20); --successes N adds N successful episodes
from the references, two thirds with a recovered error (mode_reason success_recovered_*) and one third clean, spread
round-robin over dataset families (seed 0). --index-only rebuilds the gallery / sheet from what is on disk;
--verify K probes K videos with ffprobe (duration and frame count against the reference) and checks that every file
referenced by index.html exists. Renders nothing on the GPU; frame decoding is one batched call per camera and
episode, encoding is ffmpeg libx264 crf 23 yuv420p fed with raw RGB frames over a pipe (review_video.py's approach).
Nothing here is registered with the benchmark: it reads references and writes to the Windows outputs directory only.
"""
import argparse
import csv
import html
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BENCH_DIR = Path(__file__).resolve().parent
ANNOTATE_DIR = BENCH_DIR.parent
for _p in (str(ANNOTATE_DIR), str(BENCH_DIR)):
    if _p not in sys.path:
        sys.path.append(_p)

from common import CAM_MAIN, CAM_WRIST, WIN_OUT, dump_json  # noqa: E402
from oracle_reference import BENCH, MODES, REF_DIR, ref_path  # noqa: E402

OUT_ROOT = WIN_OUT / "oracle_review"
SETS = ("heldout", "dev", "success_recovered", "success_clean", "extra")

# review palette (requested for this kit; review_video.py uses a lighter VLM-audit palette)
LABEL_COLORS = {"progress": "#3cc27a", "failure_inducing": "#e8473f", "recovery": "#f39a2b",
                "neutral": "#8d95a7", "aftermath": "#5a3d8f"}
EVENT_STYLE = {"grasp": ("up", "#f4f6fa"), "drop": ("down", "#ff5a5a"), "release": ("down", "#5fb0ff"), "attempt": ("x", "#ffffff")}
BG, FG, DIM, ACCENT = "#111722", "#e8edf5", "#aab3c5", "#ffd56b"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
CSV_COLUMNS = ["dataset", "episode_index", "failure_mode", "oracle_decisive_chunk", "oracle_cause", "human_decisive_chunk",
               "human_cause", "human_mechanism", "human_recoverable_until", "chunk_labels_ok", "notes"]
OOPSIE_CAUSES = ("reaching", "grasp", "manipulation", "sequencing_semantic", "collision", "hardware", "not_attempted", "other")


# ----------------------------------------------------------------------------------------------- colours / fonts
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def blend(c1, c2, t):
    """c1*(1-t) + c2*t for RGB tuples."""
    return tuple(int(round(a * (1 - t) + b * t)) for a, b in zip(c1, c2))


def lighter(label_color, t=0.45):
    """Lighter / dimmer tone of a label colour for multi-label chunks (blend towards the panel background)."""
    return blend(hex_to_rgb(label_color), hex_to_rgb(BG), t)


def load_fonts(scale=1.0):
    """DejaVu fonts as review_video.py, falling back to PIL's default when the TTFs are missing (tests off WSL)."""
    def tt(name, size):
        p = FONT_DIR / name
        try:
            return ImageFont.truetype(str(p), int(round(size * scale)))
        except OSError:
            return ImageFont.load_default()
    return {"title": tt("DejaVuSans-Bold.ttf", 22), "text": tt("DejaVuSans.ttf", 18), "small": tt("DejaVuSans.ttf", 15),
            "mono": tt("DejaVuSansMono-Bold.ttf", 20), "bold": tt("DejaVuSans-Bold.ttf", 18)}


# ----------------------------------------------------------------------------------------------- reference helpers
def held_by_frame(ref):
    """Per-frame (state, object) lists from held_runs ('empty' where no run covers a frame)."""
    n = int(ref["n_frames"])
    states, objects = ["empty"] * n, [None] * n
    for r in ref.get("held_runs", []):
        for i in range(int(r["start"]), min(int(r["end"]), n - 1) + 1):
            states[i], objects[i] = r["state"], r["object"]
    return states, objects


def chunk_of(ref, frame):
    for c, (a, b) in enumerate(ref["chunks"]):
        if a <= frame < b:
            return c
    return len(ref["chunks"]) - 1


def frame_x(ref, frame, x0, x1):
    """x position of a (fractional) frame index on a timeline spanning x0..x1."""
    n = max(int(ref["n_frames"]), 1)
    return x0 + float(frame) / n * (x1 - x0)


def timeline_segments(ref, x0, x1):
    """One dict per chunk: x extent, primary label, colour and whether the allowed set has more than one label."""
    segs = []
    for cl in ref["chunk_labels"]:
        c = int(cl["chunk"])
        a, b = ref["chunks"][c]
        primary = cl["primary"]
        segs.append({"chunk": c, "xa": frame_x(ref, a, x0, x1), "xb": frame_x(ref, b, x0, x1), "primary": primary,
                     "color": LABEL_COLORS[primary], "multi": len(cl["allowed"]) > 1, "allowed": list(cl["allowed"]),
                     "rule": cl["rule"], "frames": (a, b)})
    return segs


def event_markers(ref):
    """(frame, type, object) for grasp/drop/release events; the marker sits at the last_before/first_after boundary."""
    out = []
    for ev in ref.get("events", []):
        if ev["type"] in EVENT_STYLE:
            out.append((float(ev["last_before"]) + 1.0, ev["type"], ev.get("object")))
    for x in ref.get("attempts", []):  # r4: failed grasp attempts (x marker at the frame of minimum aperture)
        out.append((float(x["end"]), "attempt", None))
    return out


def in_hand(ref, frame, states, objects):
    """Text for the held-object identity at a frame: object, whether it is the target, or the last object held."""
    target = ref.get("target_slot")
    s, o = states[frame], objects[frame]
    tag = lambda obj: "target" if obj == target else ("goal object" if obj == ref.get("goal_slot") else "WRONG object")  # noqa: E731
    if s == "held" and o:
        return f"{o} ({tag(o)})"
    if s == "ambiguous" and o:
        return f"{o}? ({tag(o)}, ambiguous)"
    last = None
    for ev in ref.get("events", []):
        if ev["type"] == "grasp" and int(ev["first_after"]) <= frame:
            last = ev.get("object")
    return "none" + (f"  (last held: {last}, {tag(last)})" if last else "")


# ----------------------------------------------------------------------------------------------- timeline drawing
def draw_hatch(im, box, color, spacing=7, width=2):
    """Diagonal hatch lines inside box=(xa, y0, xb, y1), clipped to the box."""
    xa, y0, xb, y1 = (int(round(v)) for v in box)
    w, h = max(xb - xa, 1), max(y1 - y0, 1)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x in range(-h, w + h, spacing):
        d.line((x, h, x + h, 0), fill=color, width=width)
    im.paste(layer, (xa, y0), layer)


def draw_timeline(im, ref, x0, x1, y, h, playhead=None, fonts=None, decisive=True, ticks=True):
    """Chunk bar (x0..x1, rows y..y+h) coloured by primary label; multi-label chunks lighter + hatched; event markers
    above the bar; a bold frame around the decisive chunk; playhead as a white line. Returns the segment list."""
    d = ImageDraw.Draw(im)
    segs = timeline_segments(ref, x0, x1)
    for s in segs:
        if s["multi"]:
            d.rectangle((s["xa"], y, s["xb"], y + h), fill=lighter(s["color"]))
            draw_hatch(im, (s["xa"], y, s["xb"], y + h), s["color"])
        else:
            d.rectangle((s["xa"], y, s["xb"], y + h), fill=s["color"])
    d = ImageDraw.Draw(im)
    for s in segs[1:]:
        d.line((s["xa"], y, s["xa"], y + h), fill=BG, width=1)
    # event markers: triangles above the bar
    tri = 7
    for f, ty, _ in event_markers(ref):
        x = frame_x(ref, f, x0, x1)
        direction, color = EVENT_STYLE[ty]
        if direction == "x":
            d.line([(x - tri, y - 3 - 2 * tri), (x + tri, y - 3)], fill=color, width=3)
            d.line([(x - tri, y - 3), (x + tri, y - 3 - 2 * tri)], fill=color, width=3)
            continue
        base, tip = (y - 3, y - 3 - 2 * tri) if direction == "up" else (y - 3 - 2 * tri, y - 3)
        d.polygon([(x - tri, base), (x + tri, base), (x, tip)], fill=color)
    # decisive chunk: bold white frame + label
    D = ref.get("decisive_chunk")
    if decisive and D is not None and 0 <= int(D) < len(segs):
        s = segs[int(D)]
        d.rectangle((s["xa"] - 1, y - 2, s["xb"] + 1, y + h + 2), outline="white", width=3)
        d.rectangle((s["xa"] - 1, y + h + 4, s["xb"] + 1, y + h + 8), fill="white")
        if fonts:
            d.text((s["xa"], y + h + 10), f"D{int(D)}", font=fonts["small"], fill="white")
    # chunk ticks
    if ticks and fonts:
        step = 5 if len(segs) <= 40 else 10
        for s in segs:
            if s["chunk"] % step == 0:
                d.line((s["xa"], y + h + 2, s["xa"], y + h + 6), fill=DIM, width=1)
                if D is None or abs(s["chunk"] - int(D)) > 1:
                    d.text((s["xa"] + 2, y + h + 8), str(s["chunk"]), font=fonts["small"], fill=DIM)
    if playhead is not None:
        x = frame_x(ref, float(playhead) + 0.5, x0, x1)
        d.line((x, y - 4, x, y + h + 4), fill="white", width=3)
    return segs


def draw_legend(d, x, y, fonts):
    """Coloured swatches for the five labels (row 1) and the marker key (row 2, 20 px lower)."""
    x_left = x
    for name, color in LABEL_COLORS.items():
        d.rectangle((x, y + 3, x + 14, y + 17), fill=color)
        d.text((x + 19, y), name, font=fonts["small"], fill=DIM)
        x += 19 + d.textlength(name, font=fonts["small"]) + 16
    d.rectangle((x, y + 3, x + 14, y + 17), fill=lighter(LABEL_COLORS["progress"]))
    d.line((x, y + 17, x + 14, y + 3), fill=LABEL_COLORS["progress"], width=2)
    d.text((x + 19, y), "hatched = multi-label", font=fonts["small"], fill=DIM)
    x, y = x_left, y + 20
    d.polygon([(x, y + 15), (x + 12, y + 15), (x + 6, y + 4)], fill=EVENT_STYLE["grasp"][1])
    d.text((x + 16, y), "grasp", font=fonts["small"], fill=DIM)
    x += 16 + d.textlength("grasp", font=fonts["small"]) + 12
    d.polygon([(x, y + 4), (x + 12, y + 4), (x + 6, y + 15)], fill=EVENT_STYLE["drop"][1])
    d.text((x + 16, y), "drop", font=fonts["small"], fill=DIM)
    x += 16 + d.textlength("drop", font=fonts["small"]) + 12
    d.polygon([(x, y + 4), (x + 12, y + 4), (x + 6, y + 15)], fill=EVENT_STYLE["release"][1])
    d.text((x + 16, y), "release   |   white frame + D<k> = decisive chunk   |   white line = playhead", font=fonts["small"], fill=DIM)


def wrap_text(d, text, font, max_width):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


# ----------------------------------------------------------------------------------------------- frame composition
class Layout:
    def __init__(self, scale=2):
        self.scale = int(scale)
        self.cam = 256 * self.scale
        self.width = max(2 * self.cam, 1024)
        self.cam_x = (self.width - 2 * self.cam) // 2
        self.tl_top = self.cam
        self.tl_y = self.tl_top + 30      # marker row above the bar
        self.tl_h = 26
        self.tl_x0, self.tl_x1 = 24, self.width - 24
        self.text_top = self.tl_y + self.tl_h + 40
        self.height = self.text_top + 342
        if self.height % 2:
            self.height += 1


def events_text(ref):
    parts = []
    for ev in ref.get("events", []):
        parts.append(f"{ev['type']} c{ev['chunk']} f{ev['last_before']}->{ev['first_after']} {ev.get('object')}")
    for x in ref.get("close_on_nothing", []):
        parts.append(f"close_on_nothing c{x['chunk']} f{x['start']}-{x['end']}")
    for w in ref.get("wrong_object_contacts", []):
        parts.append(f"{'wrong_grasp' if w.get('grasped') else 'wrong_contact'} c{w['chunk']} f{w['start']}-{w['end']} {w['object']}")
    for c in ref.get("collisions", []):
        parts.append(f"collision c{c['chunk']} f{c['start']}-{c['end']}")
    return "; ".join(parts) or "none"


def compose_frame(ref, agent, wrist, i, layout, fonts, set_name, states, objects, fps):
    """One composed video frame (PIL RGB image) for local frame i."""
    L = layout
    n, D = int(ref["n_frames"]), ref.get("decisive_chunk")
    c = chunk_of(ref, i)
    cl = ref["chunk_labels"][c]
    a, b = ref["chunks"][c]
    im = Image.new("RGB", (L.width, L.height), BG)
    im.paste(Image.fromarray(agent).resize((L.cam, L.cam), Image.NEAREST if L.scale > 1 else Image.BILINEAR), (L.cam_x, 0))
    im.paste(Image.fromarray(wrist).resize((L.cam, L.cam), Image.NEAREST if L.scale > 1 else Image.BILINEAR), (L.cam_x + L.cam, 0))
    d = ImageDraw.Draw(im)
    # burnt-in chunk / frame counter and camera names
    tag = f"f {i:3d}  c {c:2d}"
    tw = d.textlength(tag, font=fonts["mono"])
    d.rectangle((L.cam_x + 6, 6, L.cam_x + 6 + tw + 12, 36), fill=(0, 0, 0))
    d.text((L.cam_x + 12, 9), tag, font=fonts["mono"], fill=ACCENT)
    d.rectangle((L.cam_x + L.cam + 6, 6, L.cam_x + L.cam + 76, 30), fill=(0, 0, 0))
    d.text((L.cam_x + L.cam + 12, 8), "wrist", font=fonts["small"], fill=FG)
    d.rectangle((L.cam_x + 6, L.cam - 30, L.cam_x + 90, L.cam - 6), fill=(0, 0, 0))
    d.text((L.cam_x + 12, L.cam - 28), "agentview", font=fonts["small"], fill=FG)
    if D is not None and c == int(D):
        d.rectangle((L.cam_x, 0, L.cam_x + 2 * L.cam - 1, L.cam - 1), outline=LABEL_COLORS["failure_inducing"], width=4)
    # timeline
    draw_timeline(im, ref, L.tl_x0, L.tl_x1, L.tl_y, L.tl_h, playhead=i, fonts=fonts)
    d = ImageDraw.Draw(im)
    # text panel
    y, lh = L.text_top, 24
    maxw = L.width - 2 * L.tl_x0
    outcome = "success" if ref.get("success") else "failure"
    d.text((L.tl_x0, y), f"{ref.get('reference_version', '?')} | {ref['dataset']} / episode {ref['episode_index']}   [{set_name}]   outcome: {outcome}   "
                         f"{ref.get('suite')} t{ref.get('task_id')}", font=fonts["title"], fill=FG)
    y += lh + 6
    for line in wrap_text(d, f"task: {ref['task']}", fonts["text"], maxw)[:2]:
        d.text((L.tl_x0, y), line, font=fonts["text"], fill=FG)
        y += lh
    dtxt = "none" if D is None else f"{D} (frames {ref['chunks'][int(D)][0]}-{ref['chunks'][int(D)][1] - 1})"
    d.text((L.tl_x0, y), f"failure_mode: {ref['failure_mode']}   cause: {ref.get('cause')}   decisive chunk: {dtxt}   "
                         f"events: {len(ref.get('events', []))}", font=fonts["bold"], fill="#ffb6b6")
    y += lh
    for line in wrap_text(d, f"mode_reason: {ref.get('mode_reason')}", fonts["small"], maxw)[:2]:
        d.text((L.tl_x0, y), line, font=fonts["small"], fill=DIM)
        y += lh - 4
    y += 6
    d.text((L.tl_x0, y), f"frame {i} / {n}   t = {i / fps:05.2f} s / {n / fps:.1f} s   chunk {c} / {ref['n_chunks']} "
                         f"(frames {a}-{b - 1})", font=fonts["text"], fill=FG)
    y += lh
    allowed = ", ".join(cl["allowed"])
    d.text((L.tl_x0, y), f"label: {cl['primary'].upper()}", font=fonts["bold"], fill=LABEL_COLORS[cl["primary"]])
    xoff = L.tl_x0 + d.textlength(f"label: {cl['primary'].upper()}", font=fonts["bold"]) + 18
    d.text((xoff, y), f"allowed {{{allowed}}}", font=fonts["text"], fill=FG if len(cl["allowed"]) == 1 else DIM)
    y += lh
    d.text((L.tl_x0, y), f"rule: {cl['rule']}" + ("" if cl.get("scorable", True) else "   (unscorable: not counted by the benchmark)"),
           font=fonts["text"], fill=DIM)
    y += lh
    s, o = states[i], objects[i]
    d.text((L.tl_x0, y), f"held state: {s}   object: {o or '-'}   |   in hand: {in_hand(ref, i, states, objects)}",
           font=fonts["text"], fill="#8edbfb")
    y += lh
    d.text((L.tl_x0, y), f"target: {ref.get('target_slot')}   goal: {ref.get('goal_slot') or ref.get('goal_region') or '-'}   "
                         f"stage frames: " + ", ".join(f"{k}={v}" for k, v in ref.get("stage_frames", {}).items()),
           font=fonts["small"], fill="#8edbfb")
    y += lh - 2
    for line in wrap_text(d, "events: " + events_text(ref), fonts["small"], maxw)[:3]:
        d.text((L.tl_x0, y), line, font=fonts["small"], fill=DIM)
        y += lh - 6
    draw_legend(d, L.tl_x0, L.height - 46, fonts)
    return im


# ----------------------------------------------------------------------------------------------- frames / ffmpeg
def decode_episode(ds, ep):
    """All frames of both cameras as uint8 (n, 256, 256, 3) arrays, one decoder call per camera; falls back to the
    per-frame Episode.frame path when the batched decode does not return exactly n frames."""
    try:
        from lerobot.datasets.video_utils import decode_video_frames

        ts = np.asarray(ep.col("timestamp"), np.float64).reshape(-1).tolist()
        row = ds.meta.episodes[ep.ep]
        out = []
        for key in (CAM_MAIN, CAM_WRIST):
            off = float(row[f"videos/{key}/from_timestamp"])
            path = ds.root / ds.meta.get_video_file_path(ep.ep, key)
            frames = decode_video_frames(path, [off + t for t in ts], ds.tolerance_s, ds._video_backend, return_uint8=True)
            arr = frames.numpy() if hasattr(frames, "numpy") else np.asarray(frames)
            if arr.ndim == 4 and arr.shape[1] == 3 and arr.shape[-1] != 3:
                arr = arr.transpose(0, 2, 3, 1)
            if arr.dtype != np.uint8:
                arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
            if arr.shape[0] != ep.n:
                raise ValueError(f"decoded {arr.shape[0]} frames, expected {ep.n}")
            out.append(np.ascontiguousarray(arr))
        return out[0], out[1], "batched"
    except Exception as e:  # noqa: BLE001
        print(f"  batched decode failed ({type(e).__name__}: {str(e)[:100]}); per-frame fallback")
        agent = np.zeros((ep.n, 256, 256, 3), np.uint8)
        wrist = np.zeros_like(agent)
        for i in range(ep.n):
            a, w = ep.frame(i)
            agent[i], wrist[i] = a, w
        return agent, wrist, "per_frame"


def ffmpeg_pipe(output, width, height, fps):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
           "-i", "-", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           str(output)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def render_episode(ds, ep, ref, set_name, out_dir, fps, scale):
    """Write video.mp4, poster.jpg, reference.json, review.json and index.html for one episode; returns review row."""
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    layout, fonts = Layout(scale), load_fonts()
    states, objects = held_by_frame(ref)
    agent, wrist, how = decode_episode(ds, ep)
    D = ref.get("decisive_chunk")
    poster_frame = int(ref["chunks"][int(D)][0]) if D is not None else ep.n // 2
    output = out_dir / "video.mp4"
    proc = ffmpeg_pipe(output, layout.width, layout.height, fps)
    try:
        for i in range(ep.n):
            im = compose_frame(ref, agent[i], wrist[i], i, layout, fonts, set_name, states, objects, fps)
            if i == poster_frame:
                im.save(out_dir / "poster.jpg", quality=88)
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code:
        raise RuntimeError(f"ffmpeg failed with exit code {code}")
    dump_json(ref, out_dir / "reference.json")
    row = review_row(ref, set_name, seconds=time.time() - t0, decode=how, fps=fps, poster_frame=poster_frame)
    dump_json(row, out_dir / "review.json")
    (out_dir / "index.html").write_text(episode_page(ref, row), encoding="utf-8")
    return row


def review_row(ref, set_name, seconds=None, decode=None, fps=None, poster_frame=None):
    return {"dataset": ref["dataset"], "episode_index": int(ref["episode_index"]), "set": set_name, "suite": ref.get("suite"),
            "task_id": ref.get("task_id"), "task": ref["task"], "success": bool(ref.get("success")),
            "failure_mode": ref["failure_mode"], "cause": ref.get("cause"), "decisive_chunk": ref.get("decisive_chunk"),
            "mode_reason": ref.get("mode_reason"), "n_frames": int(ref["n_frames"]), "n_chunks": int(ref["n_chunks"]),
            "fps": int(fps or ref.get("fps", 20)), "n_events": len(ref.get("events", [])), "anomalies": ref.get("anomalies", []),
            "render_seconds": None if seconds is None else round(seconds, 1), "decode": decode, "poster_frame": poster_frame,
            "dir": f"{ref['dataset']}/ep{int(ref['episode_index']):04d}"}


# ----------------------------------------------------------------------------------------------- audit sheet / protocol
def write_audit_sheet(rows, path):
    """audit_sheet.csv: one row per rendered episode, oracle columns pre-filled, human columns empty."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({"dataset": r["dataset"], "episode_index": r["episode_index"], "failure_mode": r["failure_mode"],
                        "oracle_decisive_chunk": "" if r.get("decisive_chunk") is None else r["decisive_chunk"],
                        "oracle_cause": r.get("cause") or "", "human_decisive_chunk": "", "human_cause": "", "human_mechanism": "",
                        "human_recoverable_until": "", "chunk_labels_ok": "", "notes": ""})
    return path


def protocol_markdown(n_rows, counts):
    modes = ", ".join(f"{m}={counts.get(m, 0)}" for m in list(MODES) + ["success"] if counts.get(m, 0))
    return f"""# Oracle segment annotations: human audit protocol

{n_rows} episodes rendered ({modes}). Budget: 3 minutes per episode, about {n_rows * 3 // 60} h {n_rows * 3 % 60} min in total.
Open `index.html` in this folder (filter by failure_mode or set), or the per-episode pages `<dataset>/ep<NNNN>/index.html`.
Fill `audit_sheet.csv` (one row per episode; the oracle columns are pre-filled, do not edit them).

## Per episode (3 minutes)

1. **Watch once at speed** (real time, 20 fps; a 280-step episode is 14 s). Read the task line first. Follow the two
   cameras, not the colours: which object is picked, when it leaves the gripper, whether there is another real attempt.
2. **Watch once more scrubbing the decisive region**: drag the player around the white D marker on the timeline
   (or the middle of the episode when the oracle has no decisive chunk) at quarter speed. The frame counter in the
   camera corner gives `f <frame> c <chunk>`; chunks are 10 frames = 0.5 s.
3. Fill the row:
   - `human_decisive_chunk`: the chunk whose action commits the episode to failure (the last chunk after which the
     outcome was decided: the closure that misses, the drop, the release in the wrong place, the first frame of the
     stall). Leave empty for a clean success; for a success with a recovered error give the chunk of that error.
   - `human_cause`: one of the OOPSIE causes: {", ".join(OOPSIE_CAUSES)}. (The oracle maps failure modes to
     reaching / grasp / manipulation / sequencing_semantic / collision and writes `unclear` when it cannot tell.)
   - `human_mechanism`: one sentence, geometric where possible ("closed 3 cm left of the can", "released the bowl on
     the rim of the plate, it rolled off", "pushed the basket while approaching", "never left the start pose").
   - `human_recoverable_until`: the last chunk at which a competent policy could still have completed the task in the
     remaining time (a 300-step episode with a drop at chunk 12 is usually recoverable until roughly chunk 22).
     Empty when never plausibly recoverable after the decisive chunk (or not applicable).
   - `chunk_labels_ok`: `y` when the coloured timeline is acceptable as training labels (progress green, failure-
     inducing red, recovery orange, neutral grey, aftermath purple; hatched = several labels allowed, any of them is
     fine), `n` otherwise, and say why in `notes` ("chunks 8-10 are still progress, the drop is at 11").
   - `notes`: anything else: wrong target/goal identity, an event marker that does not match the video, a success that
     is really a failure, a failure that placed the object.

## Reading the overlay

- Timeline: one cell per chunk, coloured by the oracle's primary label; a lighter hatched cell means the allowed set
  has more than one label (the text panel lists it). Triangles above the bar: grasp (white, up), drop (red, down),
  release (blue, down). White frame + `D<k>` = decisive chunk. The white line is the playhead.
- Text panel: current frame / chunk, current primary label with its allowed set and the rule that produced it,
  debounced held state (held / ambiguous / empty) and object, what is in hand and whether it is the target, and the
  full event list. Blue lines are simulator signals.
- `unscorable` chunks (unlocalised failures, `other` mode, late carries) are shown grey; the benchmark does not score
  them, but the audit should still say whether the colouring is acceptable.

## Conventions

- Chunk indices start at 0. The event chunk is the chunk of the last frame before the transition.
- "Decisive" is where the failure becomes inevitable given what the policy does afterwards, not the first mistake.
  A missed grasp followed by a successful re-grasp is a recovered error, not decisive.
- Do not look at `reference.json` before filling the human columns.
"""


# ----------------------------------------------------------------------------------------------- HTML
CSS = """body{background:#111722;color:#e8edf5;font:15px system-ui;margin:20px auto;max-width:1400px;padding:0 16px}
a{color:#8edbfb}h1{font-size:22px}table.ep{border-collapse:collapse;width:100%}table.ep>tbody>tr{border-top:1px solid #2a3547}
td{vertical-align:top;padding:10px 8px}td.media{width:420px}td.media img,td.media video{width:400px;display:block;cursor:pointer;border-radius:4px}
.meta{line-height:1.55}.tag{display:inline-block;padding:1px 7px;border-radius:9px;background:#263449;color:#ffd56b;font-size:12px;margin-left:6px}
.strip{display:flex;height:16px;margin:8px 0 4px;border-radius:3px;overflow:hidden}.strip div{height:100%;border-right:1px solid #111722;box-sizing:border-box}
.strip div.D{outline:2px solid #fff;outline-offset:-2px;z-index:1}details{margin-top:6px}summary{cursor:pointer;color:#aab3c5}
table.chunks{border-collapse:collapse;font-size:12.5px;margin-top:6px}table.chunks th,table.chunks td{border:1px solid #2a3547;padding:2px 6px;text-align:left}
table.chunks tr.D td{font-weight:bold;background:#3a1f22}.sw{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px}
select,button{padding:6px 8px;margin:2px 6px 2px 0;background:#263449;color:#e8edf5;border:1px solid #51627a;border-radius:6px}
.legend span{margin-right:14px}.small{color:#aab3c5;font-size:13px}video.big{width:100%;max-height:80vh}
.h{background:repeating-linear-gradient(135deg,rgba(17,23,34,.55) 0 3px,transparent 3px 7px)}"""


def _strip_html(ref):
    D = ref.get("decisive_chunk")
    n = max(int(ref["n_frames"]), 1)
    cells = []
    for cl in ref["chunk_labels"]:
        a, b = ref["chunks"][int(cl["chunk"])]
        cls = ("h " if len(cl["allowed"]) > 1 else "") + ("D" if D is not None and int(cl["chunk"]) == int(D) else "")
        cells.append(f'<div class="{cls.strip()}" style="width:{(b - a) / n * 100:.3f}%;background:{LABEL_COLORS[cl["primary"]]}" '
                     f'title="chunk {cl["chunk"]}: {cl["primary"]} {{{", ".join(cl["allowed"])}}} {html.escape(cl["rule"])}"></div>')
    return '<div class="strip">' + "".join(cells) + "</div>"


def _chunk_table(ref, full=False):
    D = ref.get("decisive_chunk")
    evs = defaultdict(list)
    for ev in ref.get("events", []):
        evs[int(ev["chunk"])].append(f"{ev['type']} {ev.get('object')}")
    rows = []
    for cl in ref["chunk_labels"]:
        c = int(cl["chunk"])
        a, b = ref["chunks"][c]
        cls = ' class="D"' if D is not None and c == int(D) else ""
        extra = f"<td>{a}-{b - 1}</td><td>{html.escape('; '.join(evs.get(c, [])))}</td>" if full else ""
        rows.append(f"<tr{cls}><td>{c}</td>{extra}<td><span class='sw' style='background:{LABEL_COLORS[cl['primary']]}'></span>"
                    f"{cl['primary']}</td><td>{html.escape(', '.join(cl['allowed']))}</td><td>{html.escape(cl['rule'])}</td></tr>")
    head = "<tr><th>chunk</th>" + ("<th>frames</th><th>events</th>" if full else "") + "<th>primary</th><th>allowed</th><th>rule</th></tr>"
    return f'<table class="chunks">{head}{"".join(rows)}</table>'


def legend_html():
    sw = "".join(f'<span><span class="sw" style="background:{c}"></span>{k}</span>' for k, c in LABEL_COLORS.items())
    return f'<p class="legend small">{sw}<span><span class="sw h" style="background:{LABEL_COLORS["progress"]}"></span>hatched = several allowed labels</span>' \
           f"<span>white outline = decisive chunk</span></p>"


def gallery_html(rows, refs):
    counts_mode = Counter(r["failure_mode"] for r in rows)
    counts_set = Counter(r["set"] for r in rows)
    mode_opts = "".join(f'<option value="{m}">{m} ({counts_mode[m]})</option>' for m in list(MODES) + ["success"] if counts_mode.get(m))
    set_opts = "".join(f'<option value="{s}">{s} ({counts_set[s]})</option>' for s in SETS if counts_set.get(s))
    trs = []
    for r in rows:
        ref = refs[(r["dataset"], r["episode_index"])]
        d = r["dir"]
        dec = "none" if r["decisive_chunk"] is None else r["decisive_chunk"]
        trs.append(f"""<tr class="ep" data-mode="{r['failure_mode']}" data-set="{r['set']}">
<td class="media"><div class="player" data-src="{d}/video.mp4" data-poster="{d}/poster.jpg"><img src="{d}/poster.jpg" loading="lazy" alt="poster"></div></td>
<td class="meta"><b>{html.escape(r['dataset'])} / ep {r['episode_index']}</b><span class="tag">{r['set']}</span><span class="tag">{html.escape(str(r['suite']))} t{r['task_id']}</span><br>
{html.escape(r['task'])}<br>
<b>failure_mode</b> {r['failure_mode']} &nbsp; <b>cause</b> {r['cause']} &nbsp; <b>decisive chunk</b> {dec} &nbsp; <b>n_events</b> {r['n_events']} &nbsp;
<b>frames</b> {r['n_frames']} ({r['n_chunks']} chunks)<br><span class="small">mode_reason: {html.escape(str(r['mode_reason']))}"""
                   + (f" &nbsp; anomalies: {html.escape(', '.join(r['anomalies']))}" if r.get("anomalies") else "") + f"""</span><br>
<a href="{d}/index.html">detail page</a> &middot; <a href="{d}/video.mp4">video</a> &middot; <a href="{d}/reference.json">reference.json</a>
{_strip_html(ref)}
<details><summary>chunk labels ({r['n_chunks']})</summary>{_chunk_table(ref)}</details></td></tr>""")
    return f"""<!doctype html><meta charset="utf-8"><title>Oracle segment review</title><style>{CSS}</style>
<h1>Oracle segment annotations: human review gallery</h1>
<p class="small">{len(rows)} episodes. Click a poster to play the video inline (real time, 20 fps). Protocol: <a href="audit_protocol.md">audit_protocol.md</a>,
sheet: <a href="audit_sheet.csv">audit_sheet.csv</a>. Reference builder: scripts/annotate/bench/oracle_reference.py (r2).</p>
<p>failure_mode <select id="fm"><option value="">all</option>{mode_opts}</select>
set <select id="fs"><option value="">all</option>{set_opts}</select>
<button onclick="document.querySelectorAll('details').forEach(d=>d.open=true)">expand all tables</button>
<button onclick="document.querySelectorAll('details').forEach(d=>d.open=false)">collapse all</button>
<span id="cnt" class="small"></span></p>
{legend_html()}
<table class="ep"><tbody>{"".join(trs)}</tbody></table>
<script>
const fm=document.getElementById('fm'),fs=document.getElementById('fs');
function apply(){{let k=0;document.querySelectorAll('tr.ep').forEach(tr=>{{const ok=(!fm.value||tr.dataset.mode===fm.value)&&(!fs.value||tr.dataset.set===fs.value);tr.style.display=ok?'':'none';if(ok)k++;}});document.getElementById('cnt').textContent=k+' shown';}}
fm.onchange=fs.onchange=apply;apply();
document.querySelectorAll('.player').forEach(p=>p.addEventListener('click',()=>{{if(p.querySelector('video'))return;const v=document.createElement('video');v.controls=true;v.autoplay=true;v.poster=p.dataset.poster;v.src=p.dataset.src;p.replaceChildren(v);}},{{once:true}}));
</script>"""


def episode_page(ref, row):
    D = ref.get("decisive_chunk")
    marks = [("Start", 0.0)]
    if D is not None:
        marks.append((f"Decisive chunk {D}", max(0.0, ref["chunks"][int(D)][0] / row["fps"] - 1.0)))
    for ev in ref.get("events", []):
        marks.append((f"{ev['type']} c{ev['chunk']}", max(0.0, ev["last_before"] / row["fps"] - 0.5)))
    buttons = " ".join(f'<button onclick="v.currentTime={t:.2f};v.play()">{html.escape(nm)}</button>' for nm, t in marks[:14])
    ev_rows = "".join(f"<tr><td>{ev['type']}</td><td>{ev.get('object')}</td><td>{ev['chunk']}</td><td>{ev['last_before']} -> {ev['first_after']}</td>"
                      f"<td>{ev.get('hold_frames', '')}</td><td>{ev.get('gripper_cmd_open', '')}</td></tr>" for ev in ref.get("events", []))
    held = "".join(f"<tr><td>{r['start']}-{r['end']}</td><td>{r['state']}</td><td>{r.get('object') or '-'}</td></tr>" for r in ref.get("held_runs", []))
    facts = {k: ref.get(k) for k in ("target_slot", "goal_slot", "goal_region", "target_candidates", "target_selection", "stage_frames",
                                     "close_on_nothing", "wrong_object_contacts", "collisions", "fixture_motion", "final", "anomalies")}
    return f"""<!doctype html><meta charset="utf-8"><title>{html.escape(ref['dataset'])} ep {ref['episode_index']}</title><style>{CSS}</style>
<p><a href="../../index.html">&larr; gallery</a></p>
<h1>{html.escape(ref['dataset'])} / episode {ref['episode_index']} <span class="tag">{row['set']}</span> <span class="tag">{html.escape(ref.get('reference_version', '?'))}</span></h1>
<p>{html.escape(ref['task'])}</p>
<p><b>outcome</b> {'success' if ref.get('success') else 'failure'} &nbsp; <b>failure_mode</b> {ref['failure_mode']} &nbsp; <b>cause</b> {ref.get('cause')} &nbsp;
<b>decisive chunk</b> {'none' if D is None else D} &nbsp; <b>mode_reason</b> {html.escape(str(ref.get('mode_reason')))}</p>
<video id="v" class="big" controls preload="metadata" poster="poster.jpg" src="video.mp4"></video>
<div>{buttons} <select onchange="v.playbackRate=Number(this.value)"><option value="1">Normal speed</option><option value="0.5">Half speed</option><option value="0.25">Quarter speed</option></select></div>
{_strip_html(ref)}
{legend_html()}
<h3>Events</h3><table class="chunks"><tr><th>type</th><th>object</th><th>chunk</th><th>frames</th><th>hold frames</th><th>cmd open</th></tr>{ev_rows}</table>
<h3>Chunk labels</h3>{_chunk_table(ref, full=True)}
<h3>Held runs</h3><table class="chunks"><tr><th>frames</th><th>state</th><th>object</th></tr>{held}</table>
<h3>Other reference facts</h3><pre class="small">{html.escape(json.dumps(facts, indent=1))}</pre>
<p><a href="reference.json">reference.json</a></p>"""


# ----------------------------------------------------------------------------------------------- selection
def load_set(name):
    p = BENCH / ("episodes.json" if name == "heldout" else "episodes_dev.json")
    return [(e["dataset"], int(e["episode_index"])) for e in json.loads(p.read_text())["episodes"]]


def select_successes(n, seed=0, skip=()):
    """n successful episodes from the references: round(2n/3) with a recovered error, the rest clean; round-robin over
    dataset families with a seeded permutation inside each family."""
    if n <= 0:
        return []
    rec, clean = defaultdict(list), defaultdict(list)
    skip = set(skip)
    for d in sorted(p for p in REF_DIR.iterdir() if p.is_dir()):
        fam = d.name.split("__t")[0]
        for p in sorted(d.glob("episode_*.json")):
            r = json.loads(p.read_text())
            key = (r["dataset"], int(r["episode_index"]))
            if not r.get("success") or key in skip:
                continue
            reason = str(r.get("mode_reason") or "")
            if reason.startswith("success_recovered"):
                rec[fam].append(key)
            elif reason == "success" and r.get("decisive_chunk") is None and not r.get("anomalies"):
                clean[fam].append(key)
    rng = np.random.default_rng(seed)

    def pick(pool, k):
        fams = sorted(pool)
        fams = [fams[i] for i in rng.permutation(len(fams))]
        for f in fams:
            pool[f] = [pool[f][i] for i in rng.permutation(len(pool[f]))]
        out = []
        while len(out) < k and any(pool[f] for f in fams):
            for f in fams:
                if pool[f] and len(out) < k:
                    out.append(pool[f].pop())
        return out

    n_rec = int(round(n * 2 / 3))
    recovered = pick(rec, n_rec)
    cleans = pick(clean, n - len(recovered))
    return [(k, "success_recovered") for k in recovered] + [(k, "success_clean") for k in cleans]


def scan_rows():
    """review.json rows and reference copies for everything rendered under OUT_ROOT."""
    rows, refs = [], {}
    for p in sorted(OUT_ROOT.glob("*/ep*/review.json")):
        if not (p.parent / "video.mp4").exists():
            continue
        row = json.loads(p.read_text())
        rows.append(row)
        refs[(row["dataset"], row["episode_index"])] = json.loads((p.parent / "reference.json").read_text())
    order = {s: i for i, s in enumerate(SETS)}
    modes = {m: i for i, m in enumerate(list(MODES) + ["success"])}
    rows.sort(key=lambda r: (order.get(r["set"], 9), modes.get(r["failure_mode"], 99), r["dataset"], r["episode_index"]))
    return rows, refs


def build_index():
    rows, refs = scan_rows()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "index.html").write_text(gallery_html(rows, refs), encoding="utf-8")
    write_audit_sheet(rows, OUT_ROOT / "audit_sheet.csv")
    (OUT_ROOT / "audit_protocol.md").write_text(protocol_markdown(len(rows), Counter(r["failure_mode"] for r in rows)), encoding="utf-8")
    print(f"index: {len(rows)} episodes -> {OUT_ROOT / 'index.html'}")
    return rows


def verify(k):
    """ffprobe K videos (duration = n_frames/fps, frame count = n_frames) and check that index.html references exist."""
    rows, _ = scan_rows()
    ok = True
    for r in rows[:k]:
        video = OUT_ROOT / r["dir"] / "video.mp4"
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
               "stream=nb_read_frames,duration,r_frame_rate,width,height", "-of", "json", str(video)]
        info = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)["streams"][0]
        frames, dur = int(info["nb_read_frames"]), float(info["duration"])
        want = r["n_frames"] / r["fps"]
        good = frames == r["n_frames"] and abs(dur - want) < 1.5 / r["fps"]
        ok &= good
        print(f"{'VERIFY_OK ' if good else 'VERIFY_BAD'} {r['dir']}: {frames} frames (ref {r['n_frames']}), {dur:.2f}s (ref {want:.2f}s), "
              f"{info['width']}x{info['height']} @ {info['r_frame_rate']}")
    page = (OUT_ROOT / "index.html").read_text(encoding="utf-8")
    refs = set(re.findall(r'(?:src|href|data-src|data-poster)="([^"#]+)"', page))
    missing = [p for p in refs if not p.startswith(("http", "javascript")) and not (OUT_ROOT / p).exists()]
    print(f"index.html references {len(refs)} files, missing {len(missing)}" + (": " + ", ".join(missing[:10]) if missing else ""))
    ok &= not missing
    print("VERIFY_ALL_OK" if ok else "VERIFY_FAILED")
    return ok


# ----------------------------------------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--set", choices=("heldout", "dev", "all", "none"), default="none")
    ap.add_argument("--extra", nargs="*", default=[], help="dataset:episode_index pairs")
    ap.add_argument("--successes", type=int, default=0)
    ap.add_argument("--fps", type=int, default=0, help="0 = recorder fps (real time)")
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--index-only", action="store_true")
    ap.add_argument("--verify", type=int, default=0, help="probe K videos and the index, then exit")
    args = ap.parse_args()
    if args.verify:
        sys.exit(0 if verify(args.verify) else 1)
    if args.index_only:
        build_index()
        return
    todo = []
    if args.set in ("heldout", "all"):
        todo += [(k, "heldout") for k in load_set("heldout")]
    if args.set in ("dev", "all"):
        todo += [(k, "dev") for k in load_set("dev")]
    for x in args.extra:
        ds, ep = x.rsplit(":", 1)
        todo.append(((ds, int(ep)), "extra"))
    todo += select_successes(args.successes, skip=[k for k, _ in todo])
    print(f"episodes to render: {len(todo)}  ({dict(Counter(s for _, s in todo))})  out: {OUT_ROOT}")
    by_ds = defaultdict(list)
    for key, set_name in todo:
        by_ds[key[0]].append((key[1], set_name))
    t_all = time.time()
    done, skipped, errors = [], 0, []
    from oracle_reference import _open_with_retry  # noqa: E402

    for name in sorted(by_ds):
        ds = None
        for ep_idx, set_name in sorted(by_ds[name]):
            out_dir = OUT_ROOT / name / f"ep{ep_idx:04d}"
            if (out_dir / "video.mp4").exists() and (out_dir / "review.json").exists() and not args.overwrite:
                skipped += 1
                continue
            rp = ref_path(name, ep_idx)
            if not rp.exists():
                errors.append((name, ep_idx, f"no reference {rp}"))
                continue
            ref = json.loads(rp.read_text())
            try:
                if ds is None:
                    ds = _open_with_retry(name)
                from common import Episode  # noqa: E402

                ep = Episode(ds, name, ep_idx)
                if ep.n != int(ref["n_frames"]):
                    raise ValueError(f"episode has {ep.n} frames, reference {ref['n_frames']}")
                fps = args.fps or ep.fps
                row = render_episode(ds, ep, ref, set_name, out_dir, fps, args.scale)
                done.append(row)
                print(f"RENDER_OK {name} ep{ep_idx} [{set_name}] {ref['failure_mode']} D={ref['decisive_chunk']} {ep.n} frames "
                      f"{row['render_seconds']}s ({row['decode']})  [{time.time() - t_all:.0f}s total]")
            except Exception as e:  # noqa: BLE001
                errors.append((name, ep_idx, f"{type(e).__name__}: {str(e)[:200]}"))
                print(f"RENDER_FAIL {name} ep{ep_idx}: {errors[-1][2]}")
    rows = build_index()
    print(f"\nrendered {len(done)}, skipped (existing) {skipped}, failed {len(errors)}, total {time.time() - t_all:.0f}s; "
          f"gallery rows {len(rows)}")
    cnt = Counter((r["set"], r["failure_mode"]) for r in rows)
    for s in SETS:
        ms = {m: k for (ss, m), k in cnt.items() if ss == s}
        if ms:
            print(f"  {s:18s} " + ", ".join(f"{m}={ms[m]}" for m in list(MODES) + ["success"] if m in ms))
    for name, ep_idx, msg in errors:
        print(f"  ERROR {name} ep{ep_idx}: {msg}")
    print(f"RENDER_TOTAL_SECONDS {time.time() - t_all:.0f}")


if __name__ == "__main__":
    main()
