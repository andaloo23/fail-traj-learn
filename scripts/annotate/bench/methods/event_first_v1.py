"""event_first_v1: the run_segmentation_loop.py protocol, in-process, as a benchmark method adapter.

Two independent single-frame held/empty scans (stride 5, offsets 0 and 2, both cameras at 2x, greedy), dense
refinement of the scan-A transitions (3 sampled repeats at T=0.3), wrist close-up identification of the held
object, two chunk-label passes (k=3, T=0.3, context 0 seed 7100 / context 5 seed 9100) and the
combine_local_evidence rule cascade. Scans and refinement use backend.generate one frame at a time.

decisive_chunk = chunk of the last agreed drop (null if none); cause = grasp if a drop exists, manipulation if the
last event is a release, else null. This is the honest baseline of the existing protocol.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parents[1]):  # bench/methods and scripts/annotate
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _event_first_lib as lib  # noqa: E402

CONFIG = {
    "protocol": "run_segmentation_loop.py",
    "backend": "generate",
    "batch": 1,
    "scan": {"stride": 5, "offsets": [0, 2], "scale": 2.0, "camera": "both", "temperature": 0.0, "k": 1,
             "max_new_tokens": lib.STATE_MAX_NEW_TOKENS},
    "refine": {"source": "scan_a_transitions", "margin": [2, 2], "repeats": 3, "temperature": 0.3, "scale": 2.0, "seed": lib.LAB_SEED},
    "identify": {"max_frames": 4, "scale": 2.0, "temperature": 0.0, "camera": "wrist", "prompt": "prompt.IDENTIFY_SYSTEM"},
    "chunk": {"k": 3, "temperature": 0.3, "scale": 2.0, "motion": True, "held_object_fact": False, "max_new_tokens": lib.CHUNK_MAX_NEW_TOKENS,
              "glossary": "object_slots+fixtures+target_objects"},
    "chunk_passes": [{"context": 0, "seed": 7100, "states": 0}, {"context": 5, "seed": 9100, "states": 1}],
    "events": {"min_run": 2, "agree_across_scans": True, "drop_if_cmd_gt": 0.5},
    "decisive": "chunk of the last agreed drop, else null",
    "cause": "grasp if any drop; manipulation if the last event is a release; else null",
}


def run(ep, backend, workdir, cfg=CONFIG):
    return lib.run_protocol(ep, backend, workdir, cfg, batched=False)
