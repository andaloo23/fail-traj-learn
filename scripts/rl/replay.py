"""The offline transition buffer: loads a built dataset onto the GPU and samples minibatches.

The whole libero_object corpus is ~250k transitions x 90 floats, so everything lives in device memory
and a minibatch is one index_select. Extra per-frame columns (segment labels, weights) are attached by
`labels.py` through `attach`, which keeps the segment experiments on exactly the same sampler.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ARRAYS = ("obs", "next_obs", "action", "reward", "done", "timeout", "ep_id", "frame_index")


class OfflineData:
    def __init__(self, path: str | Path, device: str = "cuda", val_frac: float = 0.05, seed: int = 0):
        self.path = Path(path)
        self.device = torch.device(device)
        self.meta = json.loads((self.path / "meta.json").read_text())
        self.episodes = pd.read_parquet(self.path / "episodes.parquet")

        raw = {k: np.load(self.path / f"{k}.npy") for k in ARRAYS}
        self.n = len(raw["obs"])
        self.obs_dim = int(self.meta["obs_dim"])
        self.act_dim = int(self.meta["action_dim"])
        self.obs_mean = np.asarray(self.meta["obs_mean"], np.float32)
        self.obs_std = np.asarray(self.meta["obs_std"], np.float32)

        t = lambda a, d: torch.as_tensor(a, dtype=d, device=self.device)  # noqa: E731
        self.obs = t(raw["obs"], torch.float32)
        self.next_obs = t(raw["next_obs"], torch.float32)
        self.action = t(raw["action"], torch.float32)
        self.reward = t(raw["reward"], torch.float32)
        self.done = t(raw["done"], torch.float32)
        self.timeout = t(raw["timeout"], torch.bool)
        self.ep_id = t(raw["ep_id"], torch.long)
        self.frame_index = t(raw["frame_index"], torch.long)
        self.extra: dict[str, torch.Tensor] = {}

        # Episode-level success, broadcast to frames: the outcome-weighted BC baselines need it and the
        # segment experiments compare against it.
        succ = self.episodes.sort_values("ep_id")["success"].to_numpy().astype(np.float32)
        self.ep_success = t(succ, torch.float32)
        self.success = self.ep_success[self.ep_id]

        # Validation split is by EPISODE: neighbouring frames are near-duplicates, so a frame-level split
        # would leak.
        rng = np.random.default_rng(seed)
        n_ep = len(self.episodes)
        perm = rng.permutation(n_ep)
        n_val = int(round(val_frac * n_ep))
        val_eps = torch.zeros(n_ep, dtype=torch.bool, device=self.device)
        val_eps[t(perm[:n_val].copy(), torch.long)] = True
        self.is_val = val_eps[self.ep_id]
        self.train_idx = torch.nonzero(~self.is_val, as_tuple=False).squeeze(-1)
        self.val_idx = torch.nonzero(self.is_val, as_tuple=False).squeeze(-1)

        # Whitening statistics come from the TRAINING episodes only. `obs_mean` / `obs_std` in meta.json
        # are computed by build_dataset.py over the whole corpus, so using them would fit a preprocessing
        # step on the held-out episodes and every validation metric would be reported through it. The
        # corpus statistics stay available above for reporting; `norm_mean` / `norm_std` are what the
        # learner is given, and train.py stores them in the checkpoint so evaluation reuses them exactly.
        train_obs = self.obs[self.train_idx]
        self.norm_mean = train_obs.mean(0).cpu().numpy().astype(np.float32)
        train_std = train_obs.std(0, unbiased=False).cpu().numpy().astype(np.float32)
        self.norm_std = np.where(train_std < 1e-3, 1.0, train_std).astype(np.float32)

    # ------------------------------------------------------------------ views
    def attach(self, name: str, values: np.ndarray | torch.Tensor, dtype=torch.float32) -> None:
        """Add a per-frame column (length n) that `sample` will return under `name`."""
        v = torch.as_tensor(np.asarray(values), dtype=dtype, device=self.device)
        if len(v) != self.n:
            raise ValueError(f"{name}: {len(v)} rows for {self.n} transitions")
        self.extra[name] = v

    def subset(self, mask: torch.Tensor) -> torch.Tensor:
        """Training indices restricted by a boolean per-frame mask (e.g. success-only BC)."""
        keep = mask[self.train_idx]
        return self.train_idx[keep]

    def sample(self, idx: torch.Tensor) -> dict[str, torch.Tensor]:
        b = {
            "obs": self.obs[idx], "next_obs": self.next_obs[idx], "action": self.action[idx],
            "reward": self.reward[idx], "done": self.done[idx], "success": self.success[idx],
            "ep_id": self.ep_id[idx], "frame_index": self.frame_index[idx], "idx": idx,
        }
        for k, v in self.extra.items():
            b[k] = v[idx]
        return b

    def batches(self, indices: torch.Tensor, batch_size: int, generator: torch.Generator):
        """Infinite stream of uniform minibatches drawn from `indices`."""
        n = len(indices)
        while True:
            pick = torch.randint(0, n, (batch_size,), device=self.device, generator=generator)
            yield self.sample(indices[pick])

    def summary(self) -> str:
        e = self.episodes
        return (f"{self.n} transitions, {len(e)} episodes "
                f"({int(e['success'].sum())} success / {int((~e['success']).sum())} failure), "
                f"obs {self.obs_dim}d act {self.act_dim}d, "
                f"train {len(self.train_idx)} / val {len(self.val_idx)} frames")
