"""oracle_rules: ORACLE-CONDITIONED baseline. The reference's events and held object + the event_first_v2 completion
rules (with never_held_cause_reaching) and NO VLM call.

This is the floor of the oracle-conditioned family: it shows how far the deterministic rules get when perception is
perfect. Any oracle_* VLM method that scores below it on chunk_labels / decisive / cause is worse than no VLM at all
on that semantic sub-task. Reads the reference file: an ablation, never a production annotator.
"""
import copy
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _oracle_lib as olib  # noqa: E402

CONFIG = {
    "family": "oracle_conditioned",
    "oracle_conditioned": True,
    "note": olib.NOTE + " oracle_rules makes no model call: it is the rules-only baseline of the family.",
    "reads_reference_keys": ["events", "held_runs", "target_slot", "n_chunks"],
    "vlm": None,
    "completion": copy.deepcopy(olib.COMPLETION),
    "expected_calls_per_episode": 0,
}


def run(ep, backend, workdir, cfg=CONFIG, reference=None, ref_dir=None):
    workdir, log, t0, ref, facts, evidence = olib.start(ep, workdir, reference, ref_dir)
    prediction, completion_evidence = olib.rules_prediction(ep, facts, cfg["completion"])
    evidence.update(completion_evidence)
    return olib.finish(cfg, prediction, evidence, log, workdir, t0)
