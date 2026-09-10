"""Join the oracle segment labels onto a built RL dataset, frame by frame.

`annotate/bench/oracle_labels.py` exports one row per recorded frame keyed by (dataset, episode_index,
frame_index). `build_dataset.py` writes transitions in exactly that order per episode, so the join is a
lookup on the episode table plus the frame index. Any transition without a label gets `label = -1` and
`q = 0`, which every segment loss treats as "no supervision here".

Per-frame arrays produced:

  seg_label   int8    index into LABELS, -1 when unlabelled
  q           float32 oracle rule-ambiguity weight (1.0 unambiguous ... 0.0 unlocalised)
  chunk       int32   the 10-step decision chunk this frame belongs to
  decisive    int32   the decisive-error chunk t*, -1 when the oracle localised none
  onset       int32   first-error chunk, -1 when none
  rho         float32 exp(-|chunk - decisive| / kappa), 1.0 when there is no decisive chunk
  cause       int8    index into CAUSES, -1 when unknown
  event       int8    index into EVENTS for the chunk's first event, repeated across the chunk
  event_at    int8    index into EVENTS for an event on THIS frame (0 = none); the reward modes use this
  event_target bool   that event acts on the episode's target object
  event_hold  int32   frames the event's hold lasts, -1 when the frame carries no event
  event_missed bool   the event is a release that did not leave the target at the goal

  labels.py --dataset object_v1 --report
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

LABELS = ("progress", "failure_inducing", "recovery", "neutral", "aftermath")
LABEL_IDX = {n: i for i, n in enumerate(LABELS)}
CAUSES = ("reaching", "grasp", "manipulation", "sequencing_semantic", "collision", "hardware", "other", "unclear")
CAUSE_IDX = {n: i for i, n in enumerate(CAUSES)}
EVENTS = ("none", "grasp", "drop", "release")
EVENT_IDX = {n: i for i, n in enumerate(EVENTS)}

# The ordinal advantage targets of proposal section 5.4: progress and recovery should have positive
# advantage, failure_inducing negative, neutral and aftermath near zero.
SIGN = np.array([+1, -1, +1, 0, 0], np.float32)


class SegmentLabels:
    """Per-frame oracle labels aligned to the rows of a built dataset."""

    def __init__(self, seg_label, q, chunk, decisive, onset, cause, event, held, source, coverage,
                 event_at=None, event_target=None, event_hold=None, event_missed=None):
        self.seg_label, self.q, self.chunk = seg_label, q, chunk
        self.decisive, self.onset, self.cause = decisive, onset, cause
        self.event, self.held = event, held
        self.source, self.coverage = source, coverage
        # Frame-localised events (added 2026-09-09). `event` above is the chunk's first event repeated
        # across the whole chunk; these four put the event on its own frame. A label export written
        # before that column existed leaves them None, and `has_event_frames` is then False.
        self.event_at, self.event_target = event_at, event_target
        self.event_hold, self.event_missed = event_hold, event_missed

    @property
    def has_event_frames(self) -> bool:
        return self.event_at is not None

    @property
    def sign(self) -> np.ndarray:
        """y_ann in {-1, 0, +1}; 0 also for unlabelled frames (they are masked by q / labelled)."""
        s = np.zeros(len(self.seg_label), np.float32)
        ok = self.seg_label >= 0
        s[ok] = SIGN[self.seg_label[ok]]
        return s

    @property
    def labelled(self) -> np.ndarray:
        return self.seg_label >= 0

    def rho(self, kappa: float) -> np.ndarray:
        """Temporal responsibility exp(-|c - t*| / kappa) in chunks; all ones when kappa <= 0."""
        if kappa <= 0:
            return np.ones(len(self.chunk), np.float32)
        r = np.ones(len(self.chunk), np.float32)
        has = self.decisive >= 0
        r[has] = np.exp(-np.abs(self.chunk[has] - self.decisive[has]).astype(np.float32) / kappa)
        return r

    def report(self) -> str:
        n = len(self.seg_label)
        lab = self.labelled
        parts = [f"source={self.source}  labelled {lab.sum()}/{n} ({lab.mean():.1%})"]
        vc = pd.Series(self.seg_label[lab]).map(dict(enumerate(LABELS))).value_counts()
        parts.append("  labels: " + ", ".join(f"{k}={v} ({v / lab.sum():.1%})" for k, v in vc.items()))
        qh = pd.Series(self.q[lab]).value_counts().sort_index()
        parts.append("  q: " + ", ".join(f"{k:g}:{v / lab.sum():.1%}" for k, v in qh.items()))
        parts.append(f"  frames with a decisive chunk: {(self.decisive >= 0).mean():.1%}")
        cvc = pd.Series(self.cause[self.cause >= 0]).map(dict(enumerate(CAUSES))).value_counts()
        parts.append("  cause: " + ", ".join(f"{k}={v}" for k, v in cvc.items()))
        parts.append("  episode coverage: " + ", ".join(f"{k}={v}" for k, v in self.coverage.items()))
        if self.has_event_frames:
            at = self.event_at > 0
            parts.append("  events on their own frame: " + ", ".join(
                f"{EVENTS[k]}={int((self.event_at == k).sum())}" for k in (1, 2, 3))
                + f"; on the target {int(self.event_target[at].sum())}"
                + f"; missed releases {int(self.event_missed.sum())}")
        else:
            parts.append("  events: no per-frame timestamps in this export (pre-2026-09-09 oracle_labels.py)")
        return "\n".join(parts)


def load(dataset_tag: str, labels_file: str = "oracle_labels.parquet") -> SegmentLabels:
    ds_dir = C.RL / "datasets" / dataset_tag
    eps = pd.read_parquet(ds_dir / "episodes.parquet")
    ep_id = np.load(ds_dir / "ep_id.npy")
    frame_index = np.load(ds_dir / "frame_index.npy")
    n = len(ep_id)

    path = C.BENCH / labels_file
    if not path.exists():
        raise SystemExit(f"{path} not found — build it with annotate/bench/oracle_labels.py")
    lab = pd.read_parquet(path)

    # Row key -> position in the built arrays. ep_id is dense over episodes.parquet, so encode the frame
    # address as ep_id * stride + frame_index and look the label rows up in one pass.
    stride = int(frame_index.max()) + 2
    pos = np.full(int(ep_id.max() + 1) * stride, -1, np.int64)
    pos[ep_id.astype(np.int64) * stride + frame_index.astype(np.int64)] = np.arange(n)

    key = eps.set_index(["dataset", "episode_index"])["ep_id"].to_dict()
    lab_ep = np.array([key.get((d, int(e)), -1) for d, e in zip(lab["dataset"], lab["episode_index"])], np.int64)
    keep = (lab_ep >= 0) & (lab["frame_index"].to_numpy() < stride - 1)
    rows = pos[lab_ep[keep] * stride + lab["frame_index"].to_numpy()[keep].astype(np.int64)]
    good = rows >= 0
    rows, sub = rows[good], lab[keep].iloc[good]

    seg_label = np.full(n, -1, np.int8)
    q = np.zeros(n, np.float32)
    chunk = np.zeros(n, np.int32)
    decisive = np.full(n, -1, np.int32)
    onset = np.full(n, -1, np.int32)
    cause = np.full(n, -1, np.int8)
    event = np.zeros(n, np.int8)
    held = np.zeros(n, bool)

    seg_label[rows] = sub["label"].map(LABEL_IDX).fillna(-1).to_numpy().astype(np.int8)
    q[rows] = sub["q"].to_numpy(np.float32)
    chunk[rows] = sub["chunk"].to_numpy(np.int32)
    decisive[rows] = sub["decisive_error_chunk"].fillna(-1).to_numpy().astype(np.int32)
    onset[rows] = sub["failure_onset_chunk"].fillna(-1).to_numpy().astype(np.int32)
    cause[rows] = sub["cause"].map(CAUSE_IDX).fillna(-1).to_numpy().astype(np.int8)
    event[rows] = sub["event_type_in_chunk"].map(EVENT_IDX).fillna(0).to_numpy().astype(np.int8)
    held[rows] = sub["held"].to_numpy(bool)

    event_at = event_target = event_hold = event_missed = None
    if "event_at_frame" in sub.columns:
        event_at = np.zeros(n, np.int8)
        event_target = np.zeros(n, bool)
        event_hold = np.full(n, -1, np.int32)
        event_missed = np.zeros(n, bool)
        event_at[rows] = sub["event_at_frame"].map(EVENT_IDX).fillna(0).to_numpy().astype(np.int8)
        event_target[rows] = sub["event_target"].to_numpy(bool)
        event_hold[rows] = sub["event_hold_frames"].to_numpy(np.int32)
        event_missed[rows] = sub["event_missed_release"].to_numpy(bool)

    covered_eps = set(np.unique(ep_id[rows]).tolist())
    coverage = {
        "episodes_labelled": len(covered_eps), "episodes_total": len(eps),
        "failures_labelled": int(eps.loc[eps["ep_id"].isin(covered_eps) & ~eps["success"]].shape[0]),
        "failures_total": int((~eps["success"]).sum()),
    }
    source = str(sub["source"].iloc[0]) if len(sub) else "none"
    return SegmentLabels(seg_label, q, chunk, decisive, onset, cause, event, held, source, coverage,
                         event_at, event_target, event_hold, event_missed)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dataset", default="object_v1")
    ap.add_argument("--labels", default="oracle_labels.parquet")
    ap.add_argument("--kappa", type=float, default=3.0)
    args = ap.parse_args()
    sl = load(args.dataset, args.labels)
    print(sl.report())
    r = sl.rho(args.kappa)
    print(f"  rho(kappa={args.kappa}): mean {r.mean():.3f}, >0.5 on {(r > 0.5).mean():.1%} of frames")
    sign = sl.sign
    print(f"  sign: +1 {(sign > 0).mean():.1%}, -1 {(sign < 0).mean():.1%}, "
          f"0 {((sign == 0) & sl.labelled).mean():.1%}")


if __name__ == "__main__":
    main()
