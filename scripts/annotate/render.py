"""Turn an episode into what the VLM sees: one labelled tile per chunk (agentview | wrist) and a per-chunk signal
table built only from observation.state and action."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    FONT = ImageFont.load_default(size=18)
    FONT_SMALL = ImageFont.load_default(size=13)
except TypeError:  # Pillow < 10.1
    FONT = FONT_SMALL = ImageFont.load_default()


def tile_frame(agent, wrist, caption, scale=1.0):
    """(512*scale)x(256*scale) tile: agentview left, wrist right, caption burned into a black bar at the top-left.
    The 256 px recordings are marginal for the VLM (a blue can read as 'blue with a red label' at 1x, correctly
    'blue and yellow' at 2x, probe_vlm.py 2026-09-07); Qwen3-VL spends one token per 32x32 px, so scale 1.5 costs
    2.25x the visual tokens of scale 1."""
    tile = Image.fromarray(np.concatenate([agent, wrist], axis=1))
    if scale != 1.0:
        tile = tile.resize((int(tile.width * scale), int(tile.height * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(tile)
    w = d.textlength(caption, font=FONT) + 10
    d.rectangle([0, 0, w, 24], fill=(0, 0, 0))
    d.text((5, 2), caption, fill=(255, 255, 0), font=FONT)
    d.line([(tile.width // 2, 0), (tile.width // 2, tile.height - 1)], fill=(0, 0, 0), width=2)
    return tile


def tile_plan(n_chunks, max_tiles):
    """Group chunks into at most max_tiles tiles: list of (chunk_a, chunk_b) inclusive ranges."""
    if n_chunks <= max_tiles:
        return [(c, c) for c in range(n_chunks)]
    edges = np.linspace(0, n_chunks, max_tiles + 1).round().astype(int)
    return [(int(edges[i]), int(edges[i + 1]) - 1) for i in range(max_tiles) if edges[i + 1] > edges[i]]


def build_tiles(ep, max_tiles=40, offset_frac=0.5, scale=1.0):
    """Explicit start/end observations for every chunk, grouped without omitting chunks.

    Each paired-camera frame is resized to half size to bound visual-token cost.
    max_tiles bounds image count, not the number of observed chunks.
    """
    tiles = []
    for a, b in tile_plan(ep.n_chunks, max_tiles):
        frames = []
        for c in range(a, b + 1):
            s, e = ep.chunks[c]
            for i in sorted({s, e - 1}):
                agent, wrist = ep.frame(i)
                frame = tile_frame(agent, wrist, f"chunk {c} step {i}", scale)
                frames.append(frame.resize((max(1, frame.width // 2), max(1, frame.height // 2)), Image.LANCZOS))
        montage = Image.new("RGB", (frames[0].width * 2, frames[0].height * ((len(frames) + 1) // 2)))
        for j, frame in enumerate(frames):
            montage.paste(frame, ((j % 2) * frame.width, (j // 2) * frame.height))
        caption = f"chunk {a}" if a == b else f"chunks {a}-{b}"
        tiles.append((caption + " (start/end frames, row order)", montage, (a, b)))
    return tiles


def build_window_tiles(ep, chunk_lo, chunk_hi, stride=2, scale=1.0):
    """Dense tiles (every `stride` steps) over chunks [chunk_lo, chunk_hi] for the landmark refinement pass."""
    tiles = []
    s = ep.chunks[chunk_lo][0]
    e = ep.chunks[chunk_hi][1]
    for i in range(s, e, stride):
        c = ep.chunk_of_frame(i)
        agent, wrist = ep.frame(i)
        caption = f"chunk {c} step {i}"
        tiles.append((caption, tile_frame(agent, wrist, caption, scale), (c, c)))
    return tiles


def chunk_signals(ep):
    """Per-chunk summary of non-privileged signals."""
    xyz = ep.eef_xyz * 100.0  # cm
    ap = ep.gripper_aperture * 100.0  # cm
    cmd = ep.gripper_cmd
    step = np.linalg.norm(np.diff(xyz, axis=0), axis=1)  # cm per step
    rows = []
    for c, (a, b) in enumerate(ep.chunks):
        seg = slice(a, b)
        sp = float(step[a : max(b - 1, a + 1)].mean()) * ep.fps if b - 1 > a else 0.0
        rows.append({
            "chunk": c, "steps": f"{a}-{b - 1}", "t_s": round(a / ep.fps, 1),
            "x": round(float(xyz[b - 1, 0]), 1), "y": round(float(xyz[b - 1, 1]), 1), "z": round(float(xyz[b - 1, 2]), 1),
            "dz": round(float(xyz[b - 1, 2] - xyz[a, 2]), 1),
            "speed_cm_s": round(sp, 1),
            "aperture_cm": round(float(ap[b - 1]), 1),
            "cmd": "CLOSE" if float(cmd[seg].mean()) > 0 else "open",
            "cmd_changed": bool(np.any(np.sign(cmd[seg][1:]) != np.sign(cmd[seg][:-1]))) if b - a > 1 else False,
        })
    return rows


def signals_table(rows):
    hdr = "chunk  steps    t(s)   eef_x  eef_y  eef_z   dz  speed(cm/s)  aperture(cm)  gripper_cmd"
    lines = [hdr]
    for r in rows:
        flag = " *" if r["cmd_changed"] else ""
        lines.append(f"{r['chunk']:>5}  {r['steps']:<8} {r['t_s']:>4}   {r['x']:>5} {r['y']:>6} {r['z']:>6} {r['dz']:>5} "
                     f"{r['speed_cm_s']:>10}   {r['aperture_cm']:>10}   {r['cmd']}{flag}")
    lines.append("(* = gripper command toggled inside the chunk)")
    return "\n".join(lines)


def contact_sheet(tiles, cols=5):
    """Preview image of all tiles for human inspection (not shown to the model)."""
    tw = max(t[1].width for t in tiles)
    th = max(t[1].height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
    for k, (_, img, _) in enumerate(tiles):
        sheet.paste(img, ((k % cols) * tw, (k // cols) * th))
    return sheet


def build_wrist_tiles(ep, chunks, scale=2.0):
    """Wrist-camera-only close-ups (middle frame of each listed chunk) for the held-object identification call."""
    tiles = []
    for c in chunks:
        a, b = ep.chunks[c]
        i = (a + b) // 2
        _, wr = ep.frame(i)
        img = Image.fromarray(wr)
        if scale != 1.0:
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        d = ImageDraw.Draw(img)
        cap = f"chunk {c}"
        d.rectangle([0, 0, d.textlength(cap, font=FONT) + 10, 24], fill=(0, 0, 0))
        d.text((5, 2), cap, fill=(255, 255, 0), font=FONT)
        tiles.append((cap, img, (c, c)))
    return tiles


def holding_chunks(rows, max_n=4, lo=0.8, hi=3.5):
    """Chunks whose end state looks like an object is squeezed (command CLOSE, aperture between lo and hi cm)."""
    held = [r["chunk"] for r in rows if r["cmd"] == "CLOSE" and lo <= r["aperture_cm"] <= hi]
    if len(held) <= max_n:
        return held
    idx = np.linspace(0, len(held) - 1, max_n).round().astype(int)
    return [held[i] for i in idx]
