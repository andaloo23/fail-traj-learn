"""Matched, reward-only IQL ablations; annotations never enter observations or actor weights."""
from __future__ import annotations

import numpy as np
import torch

from labels import LABEL_IDX

MODES = ("terminal", "failure", "productive")


def reward_array(base, labels=None, *, mode="terminal", success_scale=1.0,
                 failure_scale=0.01, productive_scale=0.01):
    """Cumulative rewards on each recorded action, including terminal actions.

    Missing labels, neutral and aftermath add zero. Productive means progress OR recovery.
    Scales are nonnegative magnitudes; no q/rho weighting or episode/chunk normalisation.
    """
    if mode not in MODES:
        raise ValueError(f"unknown reward mode: {mode}")
    scales = np.asarray([success_scale, failure_scale, productive_scale])
    if not np.isfinite(scales).all() or (scales < 0).any():
        raise ValueError("reward scales must be finite nonnegative magnitudes")
    base = np.asarray(base, dtype=np.float32)
    if base.ndim != 1 or not np.isin(base, [0, 1]).all():
        raise ValueError("base rewards must be a vector of sparse 0/1 rewards")
    out = base * success_scale
    if mode != "terminal":
        labels = np.asarray(labels)
        if labels.shape != base.shape or not np.isin(labels, [-1, *LABEL_IDX.values()]).all():
            raise ValueError("aligned per-step segment labels are required")
        out = out - failure_scale * (labels == LABEL_IDX["failure_inducing"])
        if mode == "productive":
            out = out + productive_scale * np.isin(labels, [LABEL_IDX["progress"], LABEL_IDX["recovery"]])
    return out.astype(np.float32)


def apply_rewards(args, data):
    """Validate the sparse baseline, replace only replay rewards, return an audit record."""
    if args.algo != "iql" or args.data != "all" or args.segments:
        raise ValueError("reward experiments require --algo iql --data all and no --segments")
    if data.meta.get("obs_spec") != "v2":
        raise ValueError("reward experiments require observable --obs-spec v2 data")
    if data.meta.get("bootstrap_timeout", False):
        raise ValueError("reward experiments require terminal timeouts (rebuild without --bootstrap-timeout)")
    eps = data.episodes.sort_values("ep_id")
    ep = data.ep_id.cpu().numpy()
    frame = data.frame_index.cpu().numpy()
    terminal = frame == eps["length"].to_numpy()[ep] - 1
    expected = terminal * eps["success"].to_numpy()[ep]
    base = data.reward.cpu().numpy()
    if not np.array_equal(base, expected) or not np.array_equal(data.done.cpu().numpy(), terminal):
        raise ValueError("dataset violates terminal success-only reward/done semantics")
    sl = None
    if args.reward_mode != "terminal":
        from labels import load
        sl = load(args.dataset, args.labels)
        if not sl.labelled.any():
            raise ValueError("no aligned segment labels for reward experiment")
        print(sl.report())
    shaped = reward_array(base, None if sl is None else sl.seg_label,
                         mode=args.reward_mode, success_scale=args.reward_success_scale,
                         failure_scale=args.reward_failure_scale,
                         productive_scale=args.reward_productive_scale)
    data.reward = torch.as_tensor(shaped, device=data.device)
    return {"mode": args.reward_mode, "terminal_success_count": int(expected.sum()),
            "labelled_frames": None if sl is None else int(sl.labelled.sum()),
            "label_source": None if sl is None else sl.source,
            "reward_sum": float(shaped.sum()), "reward_min": float(shaped.min()),
            "reward_max": float(shaped.max()), "changed_frames": int((shaped != base).sum())}
