"""telem_v3: held state and grasp/drop/release events from NON-privileged gripper telemetry (telemetry_held.py),
the VLM for held-object identity on 2x wrist close-ups, and the event_first_v2 completion rules for chunk labels,
decisive chunk and cause. `telem_v3c` adds the batched VLM chunk-label passes (so rules 5/6/10 can use them).

Motivation: on the dev set the visual held/empty detector was the first failing level in 15 of 20 episodes (up to
76 % of judged frames wrong; flat boxes read as empty), while the completion rules were within one chunk of the
allowed sets whenever the events were right. Gripper width is proprioception, available on real robots too.
"""
import copy
import sys
import time
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import _event_first_lib as lib  # noqa: E402
import event_first_v2 as v2  # noqa: E402
from common import dump_json  # noqa: E402
from telemetry_held import TelemetryCfg, events_from_states, held_state_from_telemetry  # noqa: E402

CONFIG = {
    "family": "telemetry_events",
    "telemetry": asdict(TelemetryCfg()),
    "identify": copy.deepcopy(v2.CONFIG["identify"]),
    "chunk": copy.deepcopy(v2.CONFIG["chunk"]),
    "chunk_passes": copy.deepcopy(v2.CONFIG["chunk_passes"]),
    "run_chunk_passes": False,
    "completion": copy.deepcopy(v2.CONFIG["completion"]),
    "batch": v2.CONFIG.get("batch", 8),
    "inputs": "observation.state[6] (finger coordinate), action[6] (gripper command), cameras for identity; no priv.*",
}


def telemetry_states_rows(states, stride=1):
    """Telemetry states in the scan-row format consumed by consensus_frames/transitions (for the chunk prompts)."""
    return [{"parsed": {"states": [{"frame": int(i), "state": str(states[i])} for i in range(0, len(states), stride)]}}]


def run(ep, backend, workdir, cfg=CONFIG):
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    log = lib.CallLog()
    t0 = time.time()
    tcfg = TelemetryCfg(**cfg["telemetry"])
    states = held_state_from_telemetry(ep.gripper_aperture, ep.gripper_cmd, tcfg)
    raw_events = events_from_states(states, ep.gripper_cmd)
    glossary = lib.episode_glossary(ep)

    held_frames = [i for i in range(len(states)) if states[i] == "held"]
    held_object, idents = None, []
    if held_frames:
        idc = cfg["identify"]
        held_object, idents = lib.identify_held_object(ep, backend, held_frames, workdir, max_frames=idc["max_frames"], scale=idc["scale"],
                                                       temperature=idc["temperature"], glossary=glossary, log=log)

    events = [{"type": e["type"], "object": held_object, "last_before": int(e["last_before"]), "first_after": int(e["first_after"]),
               "chunk": int(ep.chunk_of_frame(int(e["last_before"])))} for e in raw_events]

    passes = []
    if cfg.get("run_chunk_passes"):
        ch = cfg["chunk"]
        rows = telemetry_states_rows(states, stride=1)
        extra_facts = [lib.held_object_fact_line(held_object, list(ep.meta.get("target_objects", [])))] if ch.get("held_object_fact") else []
        for i, p in enumerate(cfg["chunk_passes"]):
            passes.append(lib.chunk_pass_many(ep, backend, rows, p["context"], p["seed"], ch["k"], workdir, kind=f"chunk_pass{i}",
                                              scale=ch["scale"], temperature=ch["temperature"], top_p=ch.get("top_p", 0.8), top_k=ch.get("top_k", 20),
                                              batch=int(ch.get("batch", 4)), motion=ch["motion"], extra_facts=extra_facts, glossary=glossary, log=log))

    n = ep.n_chunks
    prediction = {
        "held_obs": [{"frame": int(i), "state": ("uncertain" if states[i] == "uncertain" else str(states[i])), "object": None} for i in range(len(states))],
        "events": events, "held_object": held_object,
        "chunk_labels": [None] * n, "chunk_q": [0.0] * n, "decisive_chunk": None, "cause": None,
    }
    evidence = {"telemetry_cfg": asdict(tcfg), "identify": idents, "n_held_frames": len(held_frames)}
    v2.complete(ep, cfg, prediction, evidence, passes)
    prediction.update(log.as_dict())
    prediction["raw_dir"] = str(workdir)
    prediction["protocol_s"] = round(time.time() - t0, 1)
    dump_json({"config": cfg, "prediction": prediction, "evidence": evidence}, workdir / "result.json")
    return prediction

CONFIG["completion"]["never_held_cause_reaching"] = True  # never held, no close-on-nothing, no wrong-object evidence -> reaching
