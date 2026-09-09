"""Self-consistency aggregation: K parsed annotations of one episode -> one record with per-chunk confidence q."""
from collections import Counter

import numpy as np

from schema import LANDMARKS, chunk_labels, segments_from_labels


def aggregate(parsed, n_chunks, n_attempted=None):
    """Keep every valid sample. q is uncalibrated support over all attempts, including failures.

    No strict majority means zero training weight. Single-label answers are diagnostic flags, not rejected votes.
    """
    if not parsed:
        raise ValueError("at least one valid annotation is required")
    n_in = len(parsed)
    denominator = max(n_in, n_attempted or n_in)
    informative = [a for a in parsed if not (a.outcome == "failure" and len({s.label for s in a.segments}) == 1)]
    n_degenerate = n_in - len(informative)
    all_degenerate = len(informative) < 2  # every sample (or all but one) is a single-label non-answer
    K = len(parsed)
    lab = []
    conf = []
    cause_rows = []
    for a in parsed:
        l, c, cz = chunk_labels(a, n_chunks)
        lab.append(l)
        conf.append(c)
        cause_rows.append(cz)
    lab = np.array(lab, dtype=object)  # K x n
    conf = np.array(conf)

    maj, q, self_conf = [], np.zeros(n_chunks), np.zeros(n_chunks)
    q_cap = 1.0
    for c in range(n_chunks):
        cnt = Counter(lab[:, c])
        m, votes = cnt.most_common(1)[0]
        maj.append(m)
        q[c] = min(votes / denominator, q_cap)
        if votes * 2 <= denominator:
            q[c] = 0.0  # no strict majority: abstain from training supervision
        self_conf[c] = float(conf[:, c][lab[:, c] == m].mean())

    # medoid sample = the one agreeing most with the majority labelling; its free text is kept
    agree = [(lab[k] == np.array(maj, dtype=object)).mean() for k in range(K)]
    medoid = int(np.argmax(agree))

    landmarks = {}
    for key in LANDMARKS:
        vals = [getattr(a, key) for a in parsed if getattr(a, key) is not None]
        if len(vals) * 2 <= denominator:
            landmarks[key] = {"value": None, "n_votes": len(vals), "spread": None}
        else:
            landmarks[key] = {"value": int(np.median(vals)), "n_votes": len(vals), "spread": int(max(vals) - min(vals)),
                              "values": sorted(int(v) for v in vals)}

    cause_cnt = Counter(a.cause for a in parsed)
    top_cause, top_votes = cause_cnt.most_common(1)[0]
    cause = top_cause if top_votes * 2 > denominator else "unclear"
    outcome_cnt = Counter(a.outcome for a in parsed)

    # per-chunk cause: plurality among samples that labelled the chunk failure_inducing with a cause
    chunk_cause = []
    for c in range(n_chunks):
        cs = [cause_rows[k][c] for k in range(K) if lab[k, c] == "failure_inducing" and cause_rows[k][c]]
        vote = Counter(cs).most_common(1)
        chunk_cause.append(vote[0][0] if maj[c] == "failure_inducing" and vote and vote[0][1] * 2 > denominator else None)

    return {
        "k": K, "k_degenerate": n_degenerate, "all_degenerate": all_degenerate,
        "n_attempted": denominator, "n_invalid": denominator - K,
        "q_kind": "uncalibrated_vote_support", "single_label_samples": n_degenerate,
        "outcome": outcome_cnt.most_common(1)[0][0],
        "outcome_agreement": round(outcome_cnt.most_common(1)[0][1] / K, 2),
        "cause": cause,
        "cause_votes": dict(cause_cnt),
        "cause_agreement": round(top_votes / K, 2),
        "failure_symptom": parsed[medoid].failure_symptom,
        "root_cause": parsed[medoid].root_cause,
        "landmarks": landmarks,
        "chunk_label": maj,
        "chunk_q": [round(float(v), 3) for v in q],
        "chunk_self_confidence": [round(float(v), 3) for v in self_conf],
        "chunk_cause": chunk_cause,
        "segments": segments_from_labels(maj, q),
        "mean_q": round(float(q.mean()), 3),
        "sample_agreement": [round(float(a), 3) for a in agree],
        "medoid_sample": medoid,
    }


def merge_refinement(agg, refined, window=None):
    """Overwrite landmarks with the refinement-pass consensus (list of parsed dicts with landmark ints/None)."""
    out = dict(agg)
    out["landmarks_coarse"] = agg["landmarks"]
    lm = {}
    K = len(refined)
    if not K:
        return out
    for key in LANDMARKS:
        coarse = agg["landmarks"][key]["value"]
        if window is not None and key != "decisive_error" and coarse is not None and not window[0] <= coarse <= window[1]:
            lm[key] = agg["landmarks"][key]
            continue
        vals = [r[key] for r in refined if r.get(key) is not None]
        if len(vals) * 2 <= K:
            lm[key] = agg["landmarks"][key]
        else:
            lm[key] = {"value": int(np.median(vals)), "n_votes": len(vals), "spread": int(max(vals) - min(vals)),
                       "values": sorted(int(v) for v in vals), "refined": True}
    out["landmarks"] = lm
    return out


def quality_flags(agg):
    """Check structural cross-field contradictions without pretending to verify semantics."""
    flags = []
    t = agg["landmarks"]["decisive_error"]["value"]
    if t is not None and agg["chunk_label"][t] != "failure_inducing":
        flags.append("decisive_error_outside_failure_segment")
    if not any(q > 0 for q in agg["chunk_q"]):
        flags.append("no_majority_supervision")
    return flags
