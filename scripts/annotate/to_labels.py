"""Collect annotation records of one tag into a per-frame label table for the learner.

Output: $FTL_ANNOT/<tag>/labels.parquet with one row per frame:
  dataset, episode_index, frame_index (within episode), global_index (dataset row), chunk, label, q, self_conf,
  cause (episode-level), chunk_cause, decisive_error_chunk, recoverable_until_chunk, failure_onset_chunk,
  visible_failure_chunk, success, source (vlm | oracle_default | vlm_failed), tag, prompt_version
Frames of episodes whose annotation failed get label=None and q=0 so the learner can mask them.

Usage: to_labels.py <tag> [--datasets prefix ...]
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ANNOT, DATA, corrected_success, list_datasets  # noqa: E402
from aggregate import quality_flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--datasets", nargs="*", default=None)
    args = ap.parse_args()
    root = ANNOT / args.tag
    names = list_datasets(args.datasets or [])
    rows = []
    n_rec = 0
    for name in names:
        d = root / name
        if not d.exists():
            continue
        # dataset_from_index per episode, for the global row index
        import pyarrow.parquet as pq  # noqa: F401  (ensure pyarrow present)

        ep_from = {}
        meta_dir = DATA / name / "meta" / "episodes"
        for p in sorted(meta_dir.rglob("*.parquet")):
            t = pd.read_parquet(p, columns=["episode_index", "dataset_from_index"])
            ep_from.update(dict(zip(t["episode_index"].astype(int), t["dataset_from_index"].astype(int))))
        for p in sorted(d.glob("episode_*.json")):
            rec = json.load(open(p))
            if corrected_success(name, rec["episode_index"], rec["success"]) != rec["success"]:
                raise ValueError(f"{p}: stale outcome; re-annotate before exporting")
            n_rec += 1
            ann = rec.get("annotation")
            needs_review = bool(ann and (ann.get("needs_review") or quality_flags(ann)))
            lm = (ann or {}).get("landmarks", {})
            g0 = ep_from[rec["episode_index"]]
            for c, (a, b) in enumerate(rec["chunks"]):
                for i in range(a, b):
                    rows.append({
                        "dataset": name, "episode_index": rec["episode_index"], "frame_index": i, "global_index": g0 + i, "chunk": c,
                        "label": ann["chunk_label"][c] if ann else None, "q": ann["chunk_q"][c] if ann else 0.0,
                        "q_kind": ann.get("q_kind", "legacy_unspecified") if ann else "missing",
                        "needs_review": needs_review,
                        "training_q": ann["chunk_q"][c] if ann and not needs_review else 0.0,
                        "n_attempted": ann.get("n_attempted") if ann else None,
                        "n_invalid": ann.get("n_invalid") if ann else None,
                        "self_conf": ann["chunk_self_confidence"][c] if ann else 0.0,
                        "cause": ann["cause"] if ann else None, "chunk_cause": ann["chunk_cause"][c] if ann else None,
                        "decisive_error_chunk": lm.get("decisive_error", {}).get("value"),
                        "recoverable_until_chunk": lm.get("recoverable_until", {}).get("value"),
                        "failure_onset_chunk": lm.get("failure_onset", {}).get("value"),
                        "visible_failure_chunk": lm.get("visible_failure", {}).get("value"),
                        "success": rec["success"], "source": rec["source"], "tag": rec["tag"], "prompt_version": rec["prompt_version"],
                    })
    if not rows:
        sys.exit(f"no records under {root}")
    df = pd.DataFrame(rows)
    out = root / "labels.parquet"
    df.to_parquet(out, index=False)
    print(f"{n_rec} episodes, {len(df)} frames -> {out}")
    print(df.groupby(["source", "label"], dropna=False).size().to_string())
    ep = df.drop_duplicates(["dataset", "episode_index"])
    print(f"episodes by source: {ep['source'].value_counts().to_dict()}; failures with t*: "
          f"{int((~ep['success'] & ep['decisive_error_chunk'].notna()).sum())}/{int((~ep['success']).sum())}")


if __name__ == "__main__":
    main()
