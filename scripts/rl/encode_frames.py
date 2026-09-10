"""Re-render every recorded frame from its MuJoCo snapshot and cache frozen visual features.

Why re-render instead of decoding the stored videos. The recorder wrote AV1 with 4:2:0 chroma
subsampling, so a decoded frame is not the frame the renderer produced, while closed-loop evaluation
feeds the encoder raw RGB straight out of MuJoCo. Training on decoded frames and evaluating on raw ones
would introduce exactly the offline/online observation skew that `check_obs_consistency.py` currently
proves absent for the privileged spec (0.0 max error). Every frame's full MuJoCo state is in the
sidecar npz, so we restore each one and re-render it instead, and the offline features are then produced
by the same code path as the online ones.

The encoder is the frozen SigLIP vision tower of SmolVLM2-500M - the same backbone SmolVLA uses, so a
VLA actor added later shares this perception stack rather than contradicting it. It is 86M parameters
and never trained here; only the small critic and actor on top of these features are.

  encode_frames.py --verify full_shift8__t0 --episode 0     # snapshot vs stored video, on one episode
  encode_frames.py --corpus object                          # cache features for the whole corpus

Output: $FTL_RL/features/<encoder-tag>/<dataset>.npy, float16 (n_frames, 2, D), rows in the same
(episode_index, frame_index) order `build_dataset.py` flattens, plus a sidecar .json with the spec.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np  # noqa: E402
import torch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "record"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import common as C  # noqa: E402
from check_snapshot_restore_lib import restore  # noqa: E402

VLM_MODEL = "HuggingFaceTB/SmolVLM2-500M-Video-Instruct"
ENCODER_TAG = "smolvlm2_500m_siglip_256"
RENDER_SIZE = 256          # the resolution the corpus was recorded at; no resampling anywhere
N_CAMERAS = 2              # agentview, then wrist - the order build_dataset.py assumes


def camera_keys(env) -> tuple[str, str]:
    """(agentview, wrist) keys in the env's `pixels` dict, resolved exactly as record_rollouts.py does.

    The policy-facing names are set by `camera_name_mapping`, and are NOT the names the dataset stores
    them under (`observation.images.image` / `image2`); hardcoding either set silently picks the wrong
    camera or raises.
    """
    return (env.camera_name_mapping.get("agentview_image", "image"),
            env.camera_name_mapping.get("robot0_eye_in_hand_image", "image2"))


# --------------------------------------------------------------------------------- encoder
class FrozenVisionTower:
    """SmolVLM2's SigLIP tower, mean-pooled over patches. One vector per camera per frame.

    Preprocessing matches SmolVLA's (`modeling_smolvla.py`: "Normalize from range [0,1] to [-1,1] as
    expected by siglip"), so features cached here and features computed online are the same function.
    """

    def __init__(self, device="cuda", dtype=torch.bfloat16):
        from transformers import AutoModel

        self.device, self.dtype = torch.device(device), dtype
        model = AutoModel.from_pretrained(VLM_MODEL, dtype=dtype)
        tower = model.vision_model if hasattr(model, "vision_model") else model.model.vision_model
        self.tower = tower.to(self.device).eval().requires_grad_(False)
        self.dim = int(self.tower.config.hidden_size)

    @torch.inference_mode()
    def __call__(self, images: np.ndarray) -> np.ndarray:
        """(B, H, W, 3) uint8 -> (B, dim) float32."""
        x = torch.as_tensor(images, device=self.device)
        x = x.permute(0, 3, 1, 2).to(self.dtype).div_(255.0).mul_(2.0).sub_(1.0)
        out = self.tower(pixel_values=x).last_hidden_state      # (B, n_patches, dim)
        return out.mean(1).float().cpu().numpy()


class FrozenTextEmbedding:
    """Mean-pooled token embeddings of the task instruction, from the same VLM as the vision tower.

    The instruction is the one the corpus was generated with ("pick up the alphabet soup and place it in
    the basket"), and it is genuinely observable: it is the command given to the robot. Embedding it
    rather than one-hot-encoding the task id costs nothing here (there are ten distinct strings in
    libero_object) and is what lets a policy trained on this corpus be pointed at a suite whose tasks it
    has never seen.
    """

    def __init__(self, device="cuda"):
        from transformers import AutoModel, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(VLM_MODEL)
        model = AutoModel.from_pretrained(VLM_MODEL, dtype=torch.float32)
        self.emb = (model.text_model if hasattr(model, "text_model") else model.model.text_model)
        self.emb = self.emb.get_input_embeddings().to(device).eval().requires_grad_(False)
        self.device = torch.device(device)
        self.dim = int(self.emb.embedding_dim)

    @torch.inference_mode()
    def __call__(self, texts: list[str]) -> np.ndarray:
        enc = self.tok(list(texts), padding=True, truncation=True, max_length=48, return_tensors="pt")
        ids = enc["input_ids"].to(self.device)
        mask = enc["attention_mask"].to(self.device).unsqueeze(-1).float()
        vec = (self.emb(ids).float() * mask).sum(1) / mask.sum(1).clamp_min(1.0)
        return vec.cpu().numpy().astype(np.float32)


def encode_language(names: list[str], out_dir: Path, device: str) -> Path:
    """One embedding per distinct task instruction in the given datasets."""
    texts = sorted({C.sidecar(n, episode_ids(n)[0]).get("task_language", "") for n in names})
    enc = FrozenTextEmbedding(device)
    emb = enc(texts)
    out = out_dir / "language.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, texts=np.array(texts, object), emb=emb, allow_pickle=True)
    print(f"  language: {len(texts)} distinct instructions, dim {enc.dim} -> {out.name}")
    for t in texts:
        print(f"    {t!r}")
    return out


def load_language(out_dir: Path) -> dict[str, np.ndarray]:
    z = np.load(out_dir / "language.npz", allow_pickle=True)
    return {str(t): e for t, e in zip(z["texts"], z["emb"])}


# --------------------------------------------------------------------------------- rendering
def episode_ids(name: str) -> list[int]:
    return sorted(int(p.stem.split("_")[1]) for p in (C.DATA / name / "sidecar").glob("episode_*.npz"))


def reset_controllers(rs_env) -> None:
    """Re-anchor each arm controller's goal to the restored pose, before replaying a chunk.

    The OSC controller keeps `goal_pos` / `goal_ori` outside the MuJoCo state, so `set_init_state` does
    not restore them. Without this, the frames rendered inside a chunk depend on whatever the controller
    was doing before the restore - which means the cached features depend on the order episodes happened
    to be encoded in, and re-encoding the same episode in a fresh process gives different numbers.
    Re-anchoring makes the re-render a deterministic function of the snapshot alone.
    """
    for robot in getattr(rs_env, "robots", []):
        controllers = []
        if getattr(robot, "controller", None) is not None:
            controllers.append(robot.controller)
        controllers += list(getattr(robot, "part_controllers", {}).values())
        for c in controllers:
            if hasattr(c, "reset_goal"):
                c.reset_goal()


def episode_actions(name: str, ep: int) -> np.ndarray:
    import pandas as pd

    files = sorted(glob.glob(str(C.DATA / name / "data" / "**" / "*.parquet"), recursive=True))
    df = pd.concat([pd.read_parquet(f, columns=["episode_index", "frame_index", "action"])
                    for f in files], ignore_index=True)
    df = df[df["episode_index"] == ep].sort_values("frame_index", kind="stable")
    return np.stack([np.asarray(a, np.float32) for a in df["action"].to_numpy()])


def render_episode(env, name: str, ep: int, limit: int | None = None):
    """Yield (frame_index, (2, H, W, 3) uint8) for one recorded episode, re-rendered from its snapshots.

    The recorder saves a MuJoCo snapshot only at the START of each action chunk (`chunk_step == 0` in
    `record_rollouts.py`), not per frame, so a frame in the middle of a chunk has to be reached by
    restoring that chunk's snapshot and replaying the recorded actions up to it. This is the pattern
    `check_obs_consistency.py` validates. Re-restoring at every chunk boundary rather than replaying the
    whole episode from frame 0 bounds simulator divergence to one chunk (~10 steps), which is what keeps
    the re-render faithful; that script's own note is that replay error grows with horizon.

    The [::-1, ::-1] is the recorder's own convention: robosuite renders upside down and the stored
    dataset is rotated 180 degrees. Reproducing it keeps cached features in the same frame of reference.
    """
    # Start every episode from the same canonical env state. `set_init_state` restores qpos/qvel but not
    # everything mjData carries (solver warm-start among it), so without this the frames rendered inside
    # a chunk depend on which episode the worker happened to render before this one - two runs agree
    # exactly, but only if they replay the same history. Resetting first makes the cache a pure function
    # of (dataset, episode), independent of encoding order or how work was split across workers.
    env.init_state_id = 0
    env.reset(seed=0)
    meta = C.sidecar(name, ep)
    npz = np.load(C.DATA / name / "sidecar" / f"episode_{ep:06d}.npz", allow_pickle=True)
    states, starts = npz["sim_states"], npz["chunk_start_frames"]
    grip = npz["gripper_cmd"] if "gripper_cmd" in npz else None
    fixtures = meta.get("fixture_body_pose")
    actions = episode_actions(name, ep)
    cams = camera_keys(env)
    ctrl, rs_env = env._env, env._env.env
    n_frames = len(actions) if limit is None else min(limit, len(actions))

    grab = lambda o: np.stack([np.ascontiguousarray(o["pixels"][c][::-1, ::-1]) for c in cams])  # noqa: E731
    for k, start in enumerate(starts):
        reset_controllers(rs_env)
        start = int(start)
        if start >= n_frames:
            break
        end = int(starts[k + 1]) if k + 1 < len(starts) else len(actions)
        end = min(end, n_frames)
        raw = restore(ctrl, rs_env, states[k], grip[k] if grip is not None and len(grip) > k else None,
                      fixtures)
        yield start, grab(env._format_raw_obs(raw))
        for f in range(start, end - 1):
            # robosuite refuses to step a terminated episode, and `done` survives set_init_state, so a
            # success detected in one chunk would block the replay of every chunk after it. We are
            # re-rendering a trajectory that already happened, not running one, so clear it each step.
            rs_env.done = False
            obs, _, _, _, _ = env.step(actions[f])
            yield f + 1, grab(obs)


def open_env(name: str):
    """`LiberoEnv` builds its MuJoCo env lazily on the first reset, so reset once before restoring."""
    from eval_env import make_libero_env

    meta = C.sidecar(name, episode_ids(name)[0])
    env = make_libero_env(meta["suite"], int(meta["task_id"]), RENDER_SIZE, RENDER_SIZE)
    env.reset(seed=0)
    return env


# --------------------------------------------------------------------------------- verify
def decoded_video_frames(name: str, ep: int, n: int) -> np.ndarray | None:
    """The stored AV1 frames for one episode, for comparison only - never used to build features."""
    import av
    import pandas as pd

    files = sorted(glob.glob(str(C.DATA / name / "data" / "**" / "*.parquet"), recursive=True))
    t = pd.concat([pd.read_parquet(f, columns=["episode_index", "frame_index"]) for f in files],
                  ignore_index=True).sort_values(["episode_index", "frame_index"], kind="stable")
    start = int(np.flatnonzero(t["episode_index"].to_numpy() == ep)[0])
    out = []
    for cam_dir in ("observation.images.image", "observation.images.image2"):
        mp4 = sorted(glob.glob(str(C.DATA / name / "videos" / cam_dir / "**" / "*.mp4"), recursive=True))
        if not mp4:
            return None
        c = av.open(mp4[0])
        got = []
        for i, frame in enumerate(c.decode(video=0)):
            if i < start:
                continue
            got.append(frame.to_ndarray(format="rgb24"))
            if len(got) >= n:
                break
        c.close()
        out.append(np.stack(got))
    return np.stack(out, axis=1)  # (n, 2, H, W, 3)


def verify(name: str, ep: int, n_frames: int, device: str) -> int:
    """Re-render one episode, compare against the stored video in pixels and in feature space."""
    env = open_env(name)
    enc = FrozenVisionTower(device)
    t0 = time.time()
    rendered = np.stack([fr for _, fr in render_episode(env, name, ep, n_frames)])
    dt = time.time() - t0
    env.close()
    n = len(rendered)
    print(f"re-rendered {n} frames x {N_CAMERAS} cameras in {dt:.1f}s "
          f"({n / dt:.0f} frames/s, {n * N_CAMERAS / dt:.0f} images/s)")
    print(f"  full corpus (251229 frames) would take {251229 / (n / dt) / 60:.0f} min single-process")

    feat_r = enc(rendered.reshape(-1, RENDER_SIZE, RENDER_SIZE, 3)).reshape(n, N_CAMERAS, -1)
    print(f"  feature dim {feat_r.shape[-1]}, |f| mean {np.linalg.norm(feat_r, axis=-1).mean():.2f}")
    # A sanity floor: consecutive frames must not be identical, or the tower is ignoring the image.
    cos_adj = _cos(feat_r[:-1, 0], feat_r[1:, 0]).mean()
    cos_far = _cos(feat_r[: n // 2, 0], feat_r[n // 2:][: n // 2, 0]).mean()
    print(f"  cosine(adjacent frames) {cos_adj:.4f} > cosine(far apart) {cos_far:.4f}"
          f"  {'OK' if cos_adj > cos_far else '!! features are not tracking the scene'}")

    decoded = decoded_video_frames(name, ep, n)
    if decoded is None:
        print("  (no stored video to compare against)")
        return 0
    diff = np.abs(decoded.astype(np.int16) - rendered.astype(np.int16))
    print(f"\nstored AV1 video vs re-render, pixels: mean |d| {diff.mean():.2f}, "
          f"max |d| {diff.max()}, frac |d|>2: {(diff > 2).mean():.1%}")
    feat_d = enc(decoded.reshape(-1, RENDER_SIZE, RENDER_SIZE, 3)).reshape(n, N_CAMERAS, -1)
    cos = _cos(feat_r.reshape(-1, feat_r.shape[-1]), feat_d.reshape(-1, feat_d.shape[-1]))
    rel = (np.linalg.norm(feat_r - feat_d, axis=-1) / np.linalg.norm(feat_r, axis=-1)).mean()
    print(f"stored AV1 video vs re-render, features: cosine {cos.mean():.5f} "
          f"(min {cos.min():.5f}), relative L2 {rel:.4f}")
    print(f"  for scale, cosine between different frames of this episode: {cos_far:.5f}")
    return 0


def _cos(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-8)
    b = b / np.maximum(np.linalg.norm(b, axis=-1, keepdims=True), 1e-8)
    return (a * b).sum(-1)


# --------------------------------------------------------------------------------- encode
def encode_dataset(name: str, enc: FrozenVisionTower, batch: int, out_dir: Path) -> Path:
    out = out_dir / f"{name}.npy"
    if out.exists():
        print(f"  {name}: already cached, skipping")
        return out
    dropped = C.dropped_episodes(name)
    eps = [e for e in episode_ids(name) if e not in dropped]
    env = open_env(name)
    t0, parts, buf, counts = time.time(), [], [], []
    for ep in eps:
        seen = []
        for f, frames in render_episode(env, name, ep):
            seen.append(f)
            buf.append(frames)
            if len(buf) == batch:
                parts.append(_flush(buf, enc))
                buf = []
        # Features are joined onto transitions positionally, so a dropped or duplicated frame here
        # would silently shift every later frame's observation by one. Fail loudly instead.
        want = len(episode_actions(name, ep))
        if seen != list(range(want)):
            raise SystemExit(f"{name} ep{ep}: rendered frames {seen[:3]}..{seen[-3:]} "
                             f"({len(seen)}) do not tile 0..{want - 1}")
        counts.append(want)
    if buf:
        parts.append(_flush(buf, enc))
    env.close()
    feats = np.concatenate(parts).astype(np.float16)
    if len(feats) != sum(counts):
        raise SystemExit(f"{name}: {len(feats)} feature rows for {sum(counts)} frames")
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(out, feats)
    dt = time.time() - t0
    print(f"  {name}: {len(eps)} episodes, {len(feats)} frames -> {out.name} "
          f"({dt / 60:.1f} min, {len(feats) / dt:.0f} frames/s)")
    return out


def _flush(buf: list[np.ndarray], enc: FrozenVisionTower) -> np.ndarray:
    arr = np.stack(buf)                                   # (B, 2, H, W, 3)
    b, k = arr.shape[:2]
    return enc(arr.reshape(b * k, RENDER_SIZE, RENDER_SIZE, 3)).reshape(b, k, -1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus", default=None, help=f"one of {sorted(C.CORPUS)}")
    ap.add_argument("--datasets", nargs="*", default=None)
    ap.add_argument("--verify", default=None, metavar="DATASET",
                    help="compare a re-rendered episode against the stored video and exit")
    ap.add_argument("--episode", type=int, default=0)
    ap.add_argument("--frames", type=int, default=40, help="frames to check in --verify mode")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--language-only", action="store_true",
                    help="write the instruction embeddings and stop (they are cheap and shared)")
    args = ap.parse_args()

    if args.verify:
        raise SystemExit(verify(args.verify, args.episode, args.frames, args.device))
    if not args.corpus and not args.datasets:
        ap.error("give --corpus, --datasets or --verify")

    names = C.expand([args.corpus] if args.corpus else args.datasets)
    out_dir = C.RL / "features" / ENCODER_TAG
    print(f"encoding {len(names)} datasets with {ENCODER_TAG} -> {out_dir}")
    if args.language_only or not (out_dir / "language.npz").exists():
        encode_language(names, out_dir, args.device)
        if args.language_only:
            return
    enc = FrozenVisionTower(args.device)
    for name in names:
        encode_dataset(name, enc, args.batch, out_dir)
    (out_dir / "spec.json").write_text(json.dumps({
        "encoder": ENCODER_TAG, "vlm_model": VLM_MODEL, "dim": enc.dim, "cameras": ["agentview", "wrist"],
        "render_size": RENDER_SIZE, "pooling": "mean over patches", "dtype": "float16",
        "source": "re-rendered from sidecar sim_states, not decoded from the stored video",
        "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, indent=1))


if __name__ == "__main__":
    main()
