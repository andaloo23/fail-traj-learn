"""event_first_batched: event_first_v1 with the held/empty scans and dense refinement run through
backend.generate_many (left-padded batches of independent single-image prompts), and the wrist-identified
held object added to the chunk-label prompt as one extra fact line. Otherwise identical to event_first_v1.
"""
import copy
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parents[1]):  # bench/methods and scripts/annotate
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _event_first_lib as lib  # noqa: E402
from event_first_v1 import CONFIG as _V1  # noqa: E402

CONFIG = copy.deepcopy(_V1)
CONFIG.update({"backend": "generate_many", "batch": 8})
CONFIG["chunk"]["held_object_fact"] = True


def run(ep, backend, workdir, cfg=CONFIG):
    return lib.run_protocol(ep, backend, workdir, cfg, batched=True)
