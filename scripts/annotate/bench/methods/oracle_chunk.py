"""oracle_chunk: ORACLE-CONDITIONED per-chunk labels. The local_segmenter chunk prompt (k=3, T=0.3, 2x tiles, motion
line) is run with the TRUE tracker state from the reference held_runs, the true held-object fact line and the
verified-events paragraph; decisive_chunk and cause come from oracle_rules' completion so that the chunk-label task is
the only thing the VLM answers.

Isolates: given perfect held/empty tracking and identity, does the VLM label a chunk progress / failure_inducing /
recovery / neutral correctly? Evidence records which chunks the VLM and the rules disagree on and where the VLM
abstained. Reads the reference file: an ablation, never a production annotator.
"""
import copy
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _event_first_lib as lib  # noqa: E402
import _oracle_lib as olib  # noqa: E402

CONFIG = {
    "family": "oracle_conditioned",
    "oracle_conditioned": True,
    "note": olib.NOTE + " oracle_chunk asks the VLM only the per-chunk label; decisive/cause are oracle_rules'.",
    "reads_reference_keys": ["events", "held_runs", "target_slot", "n_chunks"],
    "chunk": {"k": 3, "temperature": 0.3, "scale": 2.0, "batch": 4, "context": 0, "seed": 7100, "motion": True, "top_p": 0.8, "top_k": 20,
              "sampler": "generate_many", "states": "reference held_runs (ambiguous -> uncertain)",
              "extra_facts": ["held_object_fact_line(oracle held object)", "verified events paragraph"]},
    "mapping": {"chunk_labels": "per-chunk majority (strict > 1/2 of k) label; uncertain -> null", "chunk_q": "vote support",
                "decisive_chunk, cause": "oracle_rules completion", "events, held_object": "oracle"},
    "completion": copy.deepcopy(olib.COMPLETION),
    "expected_calls_per_episode": "1 generate_many call of k * n_chunks prompts",
}


def compare(vlm_labels, rules_labels):
    """Bookkeeping: chunks where the VLM abstained, and chunks where both answered but differ."""
    abstained = [c for c, lab in enumerate(vlm_labels) if lab is None]
    disagree = [{"chunk": c, "vlm": v, "rules": r} for c, (v, r) in enumerate(zip(vlm_labels, rules_labels)) if v is not None and r is not None and v != r]
    answered = sum(1 for lab in vlm_labels if lab is not None)
    agree = answered - len(disagree)
    return {"abstained": abstained, "disagree": disagree, "n_answered": answered, "n_agree": agree,
            "agreement": round(agree / answered, 3) if answered else None}


def run(ep, backend, workdir, cfg=CONFIG, reference=None, ref_dir=None):
    workdir, log, t0, ref, facts, evidence = olib.start(ep, workdir, reference, ref_dir)
    ch = cfg["chunk"]
    rows = olib.reference_states_rows(ref, ep.n)
    targets = list(ep.meta.get("target_objects", []))
    extra_facts = [lib.held_object_fact_line(facts["held_object"], targets), evidence["facts_text"]]
    records = lib.chunk_pass_many(ep, backend, rows, int(ch["context"]), int(ch["seed"]), int(ch["k"]), workdir, kind="oracle_chunk",
                                  scale=float(ch["scale"]), temperature=float(ch["temperature"]), top_p=float(ch.get("top_p", 0.8)),
                                  top_k=int(ch.get("top_k", 20)), batch=int(ch["batch"]), motion=bool(ch["motion"]), extra_facts=extra_facts,
                                  glossary=lib.episode_glossary(ep), log=log)
    vlm_labels = [None if r.get("label") in (None, "uncertain") else str(r["label"]) for r in records]
    vlm_q = [0.0 if lab is None else round(float(r.get("support") or 0.0), 4) for lab, r in zip(vlm_labels, records)]

    rules_pred, rules_evidence = olib.rules_prediction(ep, facts, cfg["completion"])
    prediction = olib.base_prediction(ep, facts)
    prediction.update({"chunk_labels": vlm_labels, "chunk_q": vlm_q, "decisive_chunk": rules_pred["decisive_chunk"], "cause": rules_pred["cause"]})
    evidence.update({
        "vlm_chunks": [{"chunk": int(r["chunk"]), "label": r.get("label"), "votes": r.get("votes"), "support": r.get("support"),
                        "events": [s["parsed"].get("event") for s in r.get("samples", []) if "parsed" in s],
                        "observations": [s["parsed"].get("observation") for s in r.get("samples", []) if "parsed" in s]} for r in records],
        "rules_chunk_labels": rules_pred["chunk_labels"], "rules_completion_rules": rules_pred.get("completion_rules"),
        "rules_decisive_cause": [rules_pred["decisive_chunk"], rules_pred["cause"]],
        "completion": rules_evidence.get("completion"),
        "vlm_vs_rules": compare(vlm_labels, rules_pred["chunk_labels"]),
    })
    return olib.finish(cfg, prediction, evidence, log, workdir, t0)
