"""Decode original recorded cameras for the historical Sol V8 distillation export.

Extracted unchanged from the former simulator review tool. No simulator or
oracle labels are needed to decode the original recorded video.
"""
import numpy as np
from common import CAM_MAIN, CAM_WRIST


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
