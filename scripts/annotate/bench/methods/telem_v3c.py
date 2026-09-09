"""telem_v3c: telem_v3 plus the batched VLM chunk-label passes (their labels feed completion rules 5/6/10)."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import telem_v3

CONFIG = copy.deepcopy(telem_v3.CONFIG)
CONFIG["run_chunk_passes"] = True


def run(ep, backend, workdir, cfg=CONFIG):
    return telem_v3.run(ep, backend, workdir, cfg)
