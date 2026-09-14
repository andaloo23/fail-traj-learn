"""Audited annotations joined to existing obs_v2 transitions; see docs/failure_training.md."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

ROLES = ("progress", "failure_inducing", "recovery", "neutral", "aftermath")


def interval(start, end, n):
    if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= n:
        raise ValueError(f"invalid half-open interval [{start}, {end}) for length {n}")
    return slice(start, end)


def weight(record):
    value = float(record.get("weight", 1.0))
    if not np.isfinite(value) or not 0 < value <= 1:
        raise ValueError("annotation weight must be in (0, 1]")
    return value


class FailureCorpus:
    def __init__(self, dataset, manifest, allow_privileged=False):
        self.path = Path(dataset)
        self.manifest = json.loads(Path(manifest).read_text())
        m = self.manifest
        if m.get("version") != 1:
            raise ValueError("expected manifest version 1")
        self.categories, self.events = m["categories"], m["event_types"]
        for names in (self.categories, self.events):
            if not names or len(set(names)) != len(names):
                raise ValueError("class vocabularies must be nonempty and unique")
        self.chunk_size = int(m["chunk_size"])
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.meta = json.loads((self.path / "meta.json").read_text())
        if self.meta.get("spec_version") != "obs_v2" and not allow_privileged:
            raise ValueError("main model requires obs_v2; privileged diagnostics require explicit opt-in")
        self.obs = np.load(self.path / "obs.npy", mmap_mode="r")
        self.actions = np.load(self.path / "action.npy", mmap_mode="r")
        ids = np.load(self.path / "ep_id.npy")
        frames = np.load(self.path / "frame_index.npy")
        if not (len(self.obs) == len(self.actions) == len(ids) == len(frames)):
            raise ValueError("transition array lengths disagree")
        table = pd.read_parquet(self.path / "episodes.parquet")
        lookup = {(r.dataset, int(r.episode_index)): int(r.ep_id) for r in table.itertuples()}
        self.episodes = []
        seen, groups = set(), {}
        for ann in m["episodes"]:
            key = (ann["dataset"], int(ann["episode_index"]))
            if key in seen:
                raise ValueError(f"duplicate episode {key}")
            seen.add(key)
            split, group = ann["split"], ann["split_group"]
            if split not in ("train", "val", "test") or not group:
                raise ValueError("invalid split or empty split_group")
            if group in groups and groups[group] != split:
                raise ValueError(f"split group crosses partitions: {group}")
            groups[group] = split
            if not ann.get("provenance"):
                raise ValueError("annotation provenance required")
            rows = np.flatnonzero(ids == lookup[key])
            if not len(rows) or not np.array_equal(frames[rows], np.arange(len(rows))):
                raise ValueError(f"missing or unordered episode frames: {key}")
            fps = float(ann["fps"])
            if not np.isfinite(fps) or fps <= 0:
                raise ValueError("fps must be positive")
            n = (len(rows) + self.chunk_size - 1) // self.chunk_size
            role = np.full(n, -1, np.int64)
            rw = np.zeros(n, np.float32)
            cat = np.full((n, len(self.categories)), -1, np.float32)
            cw = np.zeros_like(cat)
            event = np.full((n, len(self.events)), -1, np.float32)
            ew = np.zeros_like(event)
            # Exhaustive review is explicit, never inferred from success or neutral roles.
            for coverage in ann.get("category_coverage", []):
                s = interval(coverage["start_chunk"], coverage["end_chunk_exclusive"], n)
                for name in coverage["classes"]:
                    c = self.categories.index(name)
                    cat[s, c], cw[s, c] = 0, weight(coverage)
            occupied = np.zeros(n, bool)
            for seg in ann.get("segments", []):
                s = interval(seg["start_chunk"], seg["end_chunk_exclusive"], n)
                if occupied[s].any():
                    raise ValueError(f"overlapping role segments: {key}")
                occupied[s] = True
                role[s], rw[s] = ROLES.index(seg["role"]), weight(seg)
                for name in seg.get("failure_types", []):
                    c = self.categories.index(name)
                    cat[s, c], cw[s, c] = 1, weight(seg)
            for coverage in ann.get("event_coverage", []):
                a, b = coverage["start_frame"], coverage["end_frame_exclusive"]
                interval(a, b, len(rows))
                for j in range(n):
                    lo, hi = j * self.chunk_size, min((j + 1) * self.chunk_size, len(rows))
                    if a <= lo and hi <= b:
                        for name in coverage["classes"]:
                            c = self.events.index(name)
                            event[j, c], ew[j, c] = 0, weight(coverage)
            for ev in ann.get("events", []):
                f = ev["frame"]
                interval(f, f + 1, len(rows))
                if "seconds" in ev and abs(float(ev["seconds"]) - f / fps) > 0.5 / fps:
                    raise ValueError("event frame and seconds disagree")
                j, c = f // self.chunk_size, self.events.index(ev["type"])
                event[j, c], ew[j, c] = 1, weight(ev)
            self.episodes.append(dict(key=key, split=split, group=group, rows=rows, fps=fps,
                                      role=role, role_weight=rw, category=cat, category_weight=cw,
                                      event=event, event_weight=ew, annotation=ann))
        if not self.episodes:
            raise ValueError("manifest contains no episodes")
        train = [e for e in self.episodes if e["split"] == "train"]
        if not train:
            raise ValueError("training episodes required")
        # Streaming moments over unique training chunk inputs, not overlapping windows.
        total = np.zeros(self.obs.shape[1], np.float64)
        squares = total.copy()
        count = 0
        for ep in train:
            x = np.asarray(self.obs[ep["rows"][::self.chunk_size]], np.float64)
            if not np.isfinite(x).all():
                raise ValueError("non-finite observations")
            total += x.sum(0)
            squares += (x * x).sum(0)
            count += len(x)
        self.mean = (total / count).astype(np.float32)
        std = np.sqrt(np.maximum(squares / count - (total / count) ** 2, 0))
        self.std = np.where(std < 1e-3, 1, std).astype(np.float32)

    def report(self):
        result = {}
        for ep in self.episodes:
            key = ep["split"] + "/" + ep["key"][0]
            r = result.setdefault(key, dict(episodes=0, chunks=0,
                category_positive=[0]*len(self.categories), category_negative=[0]*len(self.categories),
                event_positive=[0]*len(self.events), event_negative=[0]*len(self.events)))
            r["episodes"] += 1
            r["chunks"] += len(ep["role"])
            for name in ("category", "event"):
                for label, value in (("positive", 1), ("negative", 0)):
                    r[name + "_" + label] = (np.asarray(r[name + "_" + label]) +
                        (ep[name] == value).sum(0)).tolist()
        return result


class FailureWindows(Dataset):
    """Disjoint windows, with supervision on every causal prefix within each window."""
    def __init__(self, corpus, split, max_chunks=64):
        if max_chunks <= 0:
            raise ValueError("max_chunks must be positive")
        self.corpus, self.max_chunks = corpus, max_chunks
        self.windows = [(i, start, min(start + max_chunks, len(ep["role"])))
                        for i, ep in enumerate(corpus.episodes) if ep["split"] == split
                        for start in range(0, len(ep["role"]), max_chunks)]

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, index):
        c = self.corpus
        i, start, end = self.windows[index]
        ep = c.episodes[i]
        n, k, length = end - start, c.chunk_size, self.max_chunks
        x = np.zeros((length, c.obs.shape[1]), np.float32)
        action = np.zeros((length, k, c.actions.shape[1]), np.float32)
        amask = np.zeros((length, k), bool)
        duration = np.zeros((length, 1), np.float32)
        for pos, j in enumerate(range(start, end)):
            rows = ep["rows"][j*k:(j+1)*k]
            x[pos] = (c.obs[rows[0]] - c.mean) / c.std
            action[pos, :len(rows)] = c.actions[rows]
            amask[pos, :len(rows)] = True
            duration[pos, 0] = len(rows) / ep["fps"]
        if not np.isfinite(x).all() or not np.isfinite(action).all():
            raise ValueError("non-finite model inputs")
        out = dict(obs=x, action=action, action_valid=amask, duration=duration,
                   valid=np.arange(length) < n)
        for name in ("role", "role_weight", "event", "event_weight"):
            shape = (length,) + ep[name].shape[1:]
            out[name] = np.full(shape, -1 if name in ("role", "event") else 0, ep[name].dtype)
            out[name][:n] = ep[name][start:end]
        # Category target means present anywhere in the available WINDOW prefix.
        # Unknown earlier positions prevent a negative prefix label.
        target = ep["category"][start:end]
        weights = ep["category_weight"][start:end]
        positive = np.maximum.accumulate(np.where(target == 1, weights, 0), axis=0)
        complete = np.logical_and.accumulate(target >= 0, axis=0)
        out["category"] = np.full((length, len(c.categories)), -1, np.float32)
        out["category_weight"] = np.zeros_like(out["category"])
        out["category"][:n] = np.where(positive > 0, 1, np.where(complete, 0, -1))
        out["category_weight"][:n] = np.where(positive > 0, positive,
            np.where(complete, np.minimum.accumulate(weights, axis=0), 0))
        return {key: torch.from_numpy(value.copy()) for key, value in out.items()}
