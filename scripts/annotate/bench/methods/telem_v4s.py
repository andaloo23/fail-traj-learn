"""telem_v4s: telem_v4 (VLM veto, slot-named identification) with telem_v3's settle-based telemetry thresholds,
which had the better dev events (55 % vs 35 % for the sweep-tuned no-settle thresholds)."""
import copy
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import telem_v4
from telemetry_held import TelemetryCfg

CONFIG = copy.deepcopy(telem_v4.CONFIG)
CONFIG["telemetry"] = asdict(TelemetryCfg())
CONFIG["family"] = "telemetry_events_settle_vlm_veto"


def run(ep, backend, workdir, cfg=CONFIG):
    return telem_v4.run(ep, backend, workdir, cfg)
