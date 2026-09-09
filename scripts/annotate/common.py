"""Shared helpers for the VLM annotation pipeline: dataset access, episode views, chunking, paths.

Conventions (see docs/proposal_overview.md section 4):
  * the annotation unit is the recorder's 10-step action chunk (`chunk.index` column, 0.5 s at 20 fps);
  * the VLM only ever sees observation.images.*, observation.state, action and the episode outcome.
    priv.* columns are the ORACLE and are used only for routing (route.py) and evaluation (eval_vs_oracle.py).
"""
import json
import os
from functools import lru_cache
from functools import cached_property
from pathlib import Path

import numpy as np

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))
DATA = PROJ / "data"
ANNOT = Path(os.environ.get("FTL_ANNOT", str(PROJ / "annot")))
WIN_OUT = Path(os.environ.get("FTL_WIN_OUT", "/mnt/c/Users/LocalPC/dev/fail-traj-learn/outputs"))

CAM_MAIN = "observation.images.image"
CAM_WRIST = "observation.images.image2"


@lru_cache(maxsize=1)
def corrections():
    path = Path(__file__).resolve().parents[1] / "analysis" / "exclusions.json"
    return json.loads(path.read_text()) if path.exists() else {}


def corrected_success(name, episode_index, success):
    for entry in corrections().get(name, []):
        if entry["episode_index"] == int(episode_index):
            if entry["action"] == "relabel_success":
                return True
            if entry["action"] == "relabel_failure":
                return False
    return bool(success)


def list_datasets(prefixes):
    """Dataset names under DATA matching a name or a `<prefix>__t<k>` family. No prefixes = all finalized datasets."""
    names = sorted(p.name for p in DATA.iterdir() if (p / "meta" / "info.json").exists() and (p / "episodes.jsonl").exists())
    if not prefixes:
        return names
    return [n for n in names if any(n == a or n.startswith(a + "__t") for a in prefixes)]


def read_episodes_jsonl(name):
    rows = [json.loads(l) for l in (DATA / name / "episodes.jsonl").read_text().splitlines() if l.strip()]
    for row in rows:
        row["success"] = corrected_success(name, row["episode_index"], row["success"])
    return rows


def open_dataset(name):
    from lerobot.datasets.lerobot_dataset import LeRobotDataset  # heavy import, keep local

    return LeRobotDataset(f"fail_traj/{name}", root=DATA / name)


def to_uint8(img):
    import torch

    if isinstance(img, torch.Tensor):
        return (img.permute(1, 2, 0).numpy() * 255).clip(0, 255).astype(np.uint8)
    return np.asarray(img)


class Episode:
    """Lazy view of one recorded episode: columns, sidecar meta, chunk boundaries, decoded frames."""

    def __init__(self, ds, name, ep):
        self.ds, self.name, self.ep = ds, name, int(ep)
        self.f0 = int(ds.meta.episodes["dataset_from_index"][self.ep])
        self.f1 = int(ds.meta.episodes["dataset_to_index"][self.ep])
        self.n = self.f1 - self.f0
        self.fps = int(ds.fps)
        self.root = DATA / name
        self.meta = json.load(open(self.root / "sidecar" / f"episode_{self.ep:06d}.json"))
        self._cols = {}

    @cached_property
    def rows(self):
        return self.ds.hf_dataset.select(range(self.f0, self.f1))

    def col(self, k):
        if k not in self._cols:
            self._cols[k] = np.stack([np.asarray(x) for x in self.rows[k]])
        return self._cols[k]

    @property
    def success(self):
        return corrected_success(self.name, self.ep, self.meta["success"])

    @property
    def task(self):
        return self.meta["task_language"]

    @cached_property
    def chunks(self):
        """List of (start_frame, end_frame_exclusive) per action chunk, from the chunk.index column."""
        ci = self.col("chunk.index").reshape(-1)
        starts = [0] + [i for i in range(1, self.n) if ci[i] != ci[i - 1]]
        ends = starts[1:] + [self.n]
        return list(zip(starts, ends))

    @property
    def n_chunks(self):
        return len(self.chunks)

    def chunk_of_frame(self, i):
        for c, (a, b) in enumerate(self.chunks):
            if a <= i < b:
                return c
        return self.n_chunks - 1

    def frame(self, i):
        """(agentview, wrist) uint8 HxWx3 for local frame index i."""
        item = self.ds[self.f0 + int(i)]
        return to_uint8(item[CAM_MAIN]), to_uint8(item[CAM_WRIST])

    # --- non-privileged robot signals (what the VLM may see) -------------------------------------------
    @cached_property
    def eef_xyz(self):
        # observation.state = [eef_pos(3), eef_axis_angle(3), gripper_qpos(2)] (LeRobot LIBERO env)
        return self.col("observation.state")[:, :3].astype(np.float64)

    @cached_property
    def gripper_aperture(self):
        return self.col("observation.state")[:, 6].astype(np.float64)  # ~0.04 open, ~0.0 closed

    @cached_property
    def gripper_cmd(self):
        return self.col("action")[:, 6].astype(np.float64)  # robosuite: +1 close, -1 open


def annot_dir(tag, name):
    return ANNOT / tag / name


def annot_path(tag, name, ep):
    return annot_dir(tag, name) / f"episode_{int(ep):06d}.json"


def dump_json(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=_json_default)
    os.replace(tmp, path)


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"not serializable: {type(o)}")
