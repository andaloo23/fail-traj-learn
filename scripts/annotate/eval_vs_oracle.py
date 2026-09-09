"""Score one annotation tag against a reference tag (oracle labels, human labels, or another annotator).

Both sides use the same record layout (annotate.py output: rec["annotation"]["chunk_label"], ["landmarks"], ["cause"]).
The oracle segmenter (privileged-state rules + recovery-branching oracle) writes records in the same format under
$FTL_ANNOT/oracle/<dataset>/episode_XXXXXX.json.

Metrics: per-chunk accuracy and macro-F1 over the 5 labels (VLM-annotated episodes only), confusion matrix,
decisive_error MAE in chunks and hit rate within 1 chunk, cause accuracy (failures), calibration of q vs
correctness (5 bins, ECE), and false-alarm rate on successes (any failure_inducing / decisive_error predicted).

Usage: eval_vs_oracle.py --pred <tag> --ref <tag> [--datasets prefix ...] [--out results.json]
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ANNOT, corrected_success, list_datasets  # noqa: E402
from schema import LABELS  # noqa: E402


def load(tag, names):
    out = {}
    for name in names:
        d = ANNOT / tag / name
        if not d.exists():
            continue
        for p in d.glob("episode_*.json"):
            r = json.load(open(p))
            out[(name, r["episode_index"])] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--datasets", nargs="*", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    names = list_datasets(args.datasets or [])
    P, R = load(args.pred, names), load(args.ref, names)
    keys = sorted(set(P) & set(R))
    if not keys:
        sys.exit(f"no overlapping episodes between {args.pred} and {args.ref}")

    conf = np.zeros((5, 5), int)
    q_all, correct_all = [], []
    tstar_err, tstar_hit = [], []
    cause_ok, n_fail = 0, 0
    false_alarm, n_succ = 0, 0
    per_cause = defaultdict(lambda: [0, 0])
    n_vlm = 0
    missing_annotation = invalid_length = missing_tstar = reference_tstar = 0
    attempted = len(set(R))
    missing_records = len(set(R) - set(P))
    for k in keys:
        p, r = P[k], R[k]
        if corrected_success(k[0], k[1], r["success"]) != r["success"] or corrected_success(k[0], k[1], p["success"]) != p["success"]:
            raise ValueError(f"stale outcome for {k}; regenerate annotations")
        pa, ra = p.get("annotation"), r.get("annotation")
        if ra is None:
            raise ValueError(f"reference annotation missing for {k}")
        if pa is None:
            missing_annotation += 1
            continue
        n = len(ra["chunk_label"])
        if len(pa["chunk_label"]) != n or len(pa["chunk_q"]) != n:
            invalid_length += 1
            continue
        if p["source"] == "vlm":
            n_vlm += 1
            for c in range(n):
                i, j = LABELS.index(ra["chunk_label"][c]), LABELS.index(pa["chunk_label"][c])
                conf[i, j] += 1
                q_all.append(pa["chunk_q"][c])
                correct_all.append(i == j)
        if not r["success"]:
            n_fail += 1
            rt = ra["landmarks"]["decisive_error"]["value"]
            pt = pa["landmarks"]["decisive_error"]["value"]
            if rt is not None:
                reference_tstar += 1
                missing_tstar += int(pt is None)
            if rt is not None and pt is not None:
                tstar_err.append(abs(pt - rt))
                tstar_hit.append(abs(pt - rt) <= 1)
            ok = pa["cause"] == ra["cause"]
            cause_ok += ok
            per_cause[ra["cause"]][0] += ok
            per_cause[ra["cause"]][1] += 1
        elif p["source"] == "vlm" and "failure_inducing" not in ra["chunk_label"] and ra["landmarks"]["decisive_error"]["value"] is None:
            n_succ += 1
            if "failure_inducing" in pa["chunk_label"] or pa["landmarks"]["decisive_error"]["value"] is not None:
                false_alarm += 1

    # Missing records, failed parses and invalid lengths are also missed localizations.
    reference_tstar = sum(
        not r["success"] and r.get("annotation", {}).get("landmarks", {}).get("decisive_error", {}).get("value") is not None
        for r in R.values() if r.get("annotation")
    )
    missing_tstar = reference_tstar - len(tstar_err)
    tot = conf.sum()
    acc = conf.trace() / max(tot, 1)
    f1s = {}
    for i, lab in enumerate(LABELS):
        tp = conf[i, i]
        prec = tp / max(conf[:, i].sum(), 1)
        rec = tp / max(conf[i].sum(), 1)
        f1s[lab] = round(2 * prec * rec / max(prec + rec, 1e-9), 3)
    q_all, correct_all = np.array(q_all), np.array(correct_all, float)
    bins = np.clip((q_all * 5).astype(int), 0, 4) if len(q_all) else np.array([], int)
    calib = []
    ece = 0.0
    for b in range(5):
        m = bins == b
        if m.any():
            calib.append({"bin": f"{b / 5:.1f}-{(b + 1) / 5:.1f}", "n": int(m.sum()), "mean_q": round(float(q_all[m].mean()), 3), "acc": round(float(correct_all[m].mean()), 3)})
            ece += m.mean() * abs(q_all[m].mean() - correct_all[m].mean())
    res = {
        "reference_episodes": attempted, "missing_records": missing_records,
        "failed_annotations": missing_annotation, "invalid_lengths": invalid_length,
        "missing_tstar": missing_tstar, "reference_tstar": reference_tstar,
        "tstar_within_1_including_missing": round(sum(tstar_hit) / reference_tstar, 3) if reference_tstar else None,
        "success_false_alarm_population": "VLM evaluated reference-clean successes only",
        "pred": args.pred, "ref": args.ref, "episodes": len(keys), "vlm_episodes": n_vlm, "chunks": int(tot),
        "chunk_accuracy": round(float(acc), 3), "macro_f1": round(float(np.mean(list(f1s.values()))), 3), "f1": f1s,
        "confusion_rows_ref_cols_pred": {LABELS[i]: dict(zip(LABELS, conf[i].tolist())) for i in range(5)},
        "tstar_mae_chunks": round(float(np.mean(tstar_err)), 2) if tstar_err else None,
        "tstar_within_1": round(float(np.mean(tstar_hit)), 3) if tstar_hit else None, "tstar_pairs": len(tstar_err),
        "cause_accuracy": round(cause_ok / max(n_fail, 1), 3), "failures": n_fail,
        "cause_accuracy_by_ref_cause": {c: f"{v[0]}/{v[1]}" for c, v in per_cause.items()},
        "success_false_alarm_rate": round(false_alarm / max(n_succ, 1), 3), "successes": n_succ,
        "calibration": calib, "ece": round(float(ece), 3),
        "pred_label_dist": dict(Counter(l for r in P.values() if r.get("annotation") for l in r["annotation"]["chunk_label"])),
    }
    print(json.dumps(res, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
