"""telem_v4nv: telem_v4 thresholds without the VLM veto (isolates the effect of the tuned telemetry thresholds)."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import telem_v4

CONFIG = copy.deepcopy(telem_v4.CONFIG)
CONFIG["veto"]["enabled"] = False
CONFIG["family"] = "telemetry_events_tuned"


def run(ep, backend, workdir, cfg=CONFIG):
    return telem_v4.run(ep, backend, workdir, cfg)
