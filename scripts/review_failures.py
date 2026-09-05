"""Export contact sheets (and optionally side-by-side videos) of episodes from a recorded dataset,
with privileged signals drawn under the frames, for quick human triage of failures.

Usage:
  review_failures.py <dataset_name> [--all] [--max N] [--video] [--frames K]
    --all     include successful episodes too (default: failures only)
    --max N   at most N episodes (default 20)
    --video   also write a side-by-side mp4 (agent | wrist) per episode
    --frames  number of frames per contact sheet (default 10)
Outputs go to C:\\Users\\LocalPC\\dev\\fail-traj-learn\\outputs\\review\\<dataset_name>\\
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw

from lerobot.datasets.lerobot_dataset import LeRobotDataset

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))
WIN_OUT = Path(os.environ.get("FTL_WIN_OUT", "/mnt/c/Users/LocalPC/dev/fail-traj-learn/outputs")) / "review"


def to_uint8(img):
    if isinstance(img, torch.Tensor):
        return (img.permute(1, 2, 0).numpy() * 255).clip(0, 255).astype(np.uint8)
    return np.asarray(img)


def signal_strip(width, height, series, colors, labels):
    """Draw normalized time series as a small strip image."""
    im = Image.new("RGB", (width, height), (25, 25, 25))
    d = ImageDraw.Draw(im)
    n = len(series[0])
    for s, c in zip(series, colors):
        s = np.asarray(s, dtype=float)
        lo, hi = float(np.nanmin(s)), float(np.nanmax(s))
        rng = hi - lo if hi > lo else 1.0
        pts = [(int(i / max(n - 1, 1) * (width - 1)), int(height - 4 - (v - lo) / rng * (height - 8))) for i, v in enumerate(s)]
        d.line(pts, fill=c, width=1)
    x = 4
    for lab, c in zip(labels, colors):
        d.text((x, 2), lab, fill=c)
        x += 9 * len(lab)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max", type=int, default=20)
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--frames", type=int, default=10)
    args = ap.parse_args()

    root = PROJ / "data" / args.dataset
    ds = LeRobotDataset(f"fail_traj/{args.dataset}", root=root)
    out_dir = WIN_OUT / args.dataset
    out_dir.mkdir(parents=True, exist_ok=True)

    eps = [json.loads(l) for l in (root / "episodes.jsonl").read_text().splitlines() if l.strip()]
    chosen = [e for e in eps if args.all or not e["success"]][: args.max]
    print(f"{args.dataset}: {len(eps)} episodes, {sum(not e['success'] for e in eps)} failures; reviewing {len(chosen)}")

    for e in chosen:
        ep = e["episode_index"]
        f0 = int(ds.meta.episodes["dataset_from_index"][ep])
        f1 = int(ds.meta.episodes["dataset_to_index"][ep])
        n = f1 - f0
        rows = ds.hf_dataset.select(range(f0, f1))
        col = lambda k: np.stack([np.asarray(x) for x in rows[k]])  # noqa: E731
        meta = json.load(open(root / "sidecar" / f"episode_{ep:06d}.json"))
        target = col("priv.target_mask")[0]
        tslot = int(np.flatnonzero(target)[0]) if target.any() else 0
        grasp = col("priv.obj_grasped")[:, tslot]
        support = col("priv.obj_support_contact")[:, tslot]
        gcon = col("priv.obj_gripper_contact")[:, tslot]
        z = col("priv.obj_pos").reshape(n, -1, 3)[:, tslot, 2]
        eefz = col("priv.eef_pos")[:, 2]
        arm = col("priv.arm_contacts").reshape(-1)
        gstat = col("priv.gripper_static_contacts").reshape(-1)
        grip = col("observation.state")[:, 6]  # gripper finger qpos (open ~0.04, closed ~0.0)

        idxs = np.linspace(0, n - 1, args.frames).round().astype(int)
        tiles = []
        for i in idxs:
            item = ds[f0 + int(i)]
            a = to_uint8(item["observation.images.image"])
            w = to_uint8(item["observation.images.image2"])
            tile = Image.fromarray(np.concatenate([a, w], axis=0))  # 512 x 256
            d = ImageDraw.Draw(tile)
            tag = f"f{i} g={int(grasp[i])} s={int(support[i])} c={int(gcon[i])}"
            if arm[i] > 0:
                tag += " ARM"
            if gstat[i] > 0:
                tag += " GST"
            d.rectangle([0, 0, 256, 14], fill=(0, 0, 0))
            d.text((3, 1), tag, fill=(255, 255, 0))
            tiles.append(tile)
        sheet_w = 256 * len(tiles)
        sheet = Image.new("RGB", (sheet_w, 512 + 22 + 70), (0, 0, 0))
        d = ImageDraw.Draw(sheet)
        hdr = (f"ep {ep} | {meta['source']} | {meta['suite']}[{meta['task_id']}] '{meta['task_language']}' | "
               f"init={meta['init_mode']} | success={meta['success']} len={n} | target={meta['object_slots'][tslot] if tslot < len(meta['object_slots']) else '?'}")
        d.text((4, 4), hdr[:sheet_w // 6], fill=(255, 255, 255))
        for k, t in enumerate(tiles):
            sheet.paste(t, (k * 256, 22))
        strip = signal_strip(sheet_w, 70,
                             [z, eefz, grasp, support, grip, np.minimum(arm + gstat, 1)],
                             [(255, 80, 80), (80, 160, 255), (80, 255, 80), (200, 200, 200), (255, 200, 0), (255, 0, 255)],
                             ["target_z", "eef_z", "grasp", "support", "gripper", "collision"])
        sheet.paste(strip, (0, 512 + 22))
        sheet.save(out_dir / f"ep{ep:04d}_{'ok' if e['success'] else 'FAIL'}_{meta['suite']}_{meta['task_id']}.png")

        if args.video:
            frames_dir = out_dir / f"_frames_ep{ep:04d}"
            frames_dir.mkdir(exist_ok=True)
            for i in range(n):
                item = ds[f0 + i]
                a = to_uint8(item["observation.images.image"])
                w = to_uint8(item["observation.images.image2"])
                Image.fromarray(np.concatenate([a, w], axis=1)).save(frames_dir / f"{i:05d}.png")
            mp4 = out_dir / f"ep{ep:04d}_{'ok' if e['success'] else 'FAIL'}_{meta['suite']}_{meta['task_id']}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(int(ds.fps)), "-i", str(frames_dir / "%05d.png"),
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", str(mp4)], check=False)
            for p in frames_dir.glob("*.png"):
                p.unlink()
            frames_dir.rmdir()
        print(f"  ep {ep}: success={e['success']} len={n} target={meta['object_slots'][tslot] if tslot < len(meta['object_slots']) else '?'} "
              f"grasp_frames={int(grasp.sum())} airborne={int((support == 0).sum())} arm_contacts={int((arm > 0).sum())}")
    print(f"wrote to {out_dir}")


if __name__ == "__main__":
    main()
