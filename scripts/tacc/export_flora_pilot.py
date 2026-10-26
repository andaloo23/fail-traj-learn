"""Export full-rate observable review-pack cameras as lossless MP4s for FLORA.

No annotations, terminal outcomes, or simulator state enter either jobs file.
Requires numpy and PyAV; reuse the existing WSL LeRobot environment.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_video(path, frames, fps):
    import av
    with av.open(str(path), "w") as container:
        stream = container.add_stream("libx264rgb", rate=Fraction(str(fps)))
        stream.width, stream.height = frames.shape[2], frames.shape[1]
        stream.pix_fmt = "rgb24"
        stream.options = {"crf": "0", "preset": "fast"}
        for image in frames:
            for packet in stream.encode(av.VideoFrame.from_ndarray(image, format="rgb24")):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    with av.open(str(path)) as container:
        video = container.streams.video[0]
        if video.average_rate != Fraction(str(fps)):
            raise ValueError(f"Frame rate changed: {path}")
        decoded = [frame.to_ndarray(format="rgb24") for frame in container.decode(video)]
    import numpy as np
    if len(decoded) != len(frames) or not np.array_equal(np.stack(decoded), frames):
        raise ValueError(f"Lossless roundtrip failed: {path}")


def export(source, out, ids):
    import numpy as np
    if out.exists():
        raise ValueError(f"Use a new output directory: {out}")
    out.mkdir(parents=True)
    rewards, captions, audit = [], [], []
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate episode IDs")
    for name in ids:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", name) or name in (".", ".."):
            raise ValueError(f"Invalid episode ID: {name}")
        folder = source / name
        obs = json.loads((folder / "observable.json").read_text(encoding="utf-8"))
        n, fps = obs["n_frames"], obs["fps"]
        if n < 2 or fps < 4 or n / fps > 120:
            raise ValueError(f"{name}: outside native pipeline duration/FPS limits")
        dest = out / "videos" / name
        dest.mkdir(parents=True)
        videos = []
        with np.load(folder / "cameras.npz", allow_pickle=False) as cameras:
            for key in ("agent", "wrist"):
                frames = cameras[key]
                if frames.dtype != np.uint8 or frames.ndim != 4 or frames.shape[0] != n or frames.shape[-1] != 3:
                    raise ValueError(f"{name}: invalid full-rate {key} array")
                path = dest / (key + ".mp4")
                write_video(path, frames, fps)
                if path.stat().st_size > 256 * 1024**2:
                    raise ValueError(f"{name}: video exceeds native 256 MiB limit")
                videos.append(path.relative_to(out).as_posix())
        rewards.append(dict(id=name, task=obs["task"], videos=videos))
        # LIBERO has two views, while native robot caption profiles accept one or three.
        # Use the robot YAM single-main-camera path; never duplicate a wrist as a third view.
        captions.append(dict(id=name, video=videos[0], profile="yam", instruction=obs["task"]))
        audit.append(dict(id=name, n_frames=n, fps=fps,
                          source_observable_sha256=digest(folder / "observable.json"),
                          source_cameras_sha256=digest(folder / "cameras.npz"),
                          videos={v: digest(out / v) for v in videos}))
        print(f"{name}: verified {n} frames x 2 cameras at {fps} FPS", flush=True)
    for filename, rows in (("reward_jobs.jsonl", rewards), ("caption_jobs.jsonl", captions)):
        (out / filename).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (out / "provenance.json").write_text(json.dumps(dict(
        episodes=audit, encoding="lossless libx264rgb, exact RGB roundtrip verified",
        reward_camera_order=["agent", "wrist"], caption_camera="agent only",
        use="development pilot, previously inspected episodes; not a held-out benchmark",
        human_verified=False), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("gpt6_v3_12_episode_review_pack/episodes"))
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--ids", nargs="+", default=[f"R{i:03d}" for i in range(1, 13)])
    a = p.parse_args()
    export(a.source.resolve(), a.out.resolve(), a.ids)
