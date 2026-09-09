"""telem_v4: telemetry holds (sweep-tuned thresholds: lo 0.6 cm, hi 3.4 cm, min run 8, no settle test) as the event
skeleton, a VLM VETO on each telemetry hold (3 paired close-ups inside the run; the hold is discarded only if every
verdict is "empty"), held-object identity from the middles of the surviving holds, then the v2 completion rules.

Why this shape: telem_v3 (frame-level telemetry, default thresholds) had the best dev events (55 %) but produced
spurious in/out flickers; fused_v4 (CLOSE-command runs verified by a 2-of-3 VLM vote) rejected real holds because
the command often goes CLOSE long before the grasp, so 2 of its 3 verification frames were pre-grasp. Verifying
inside the telemetry hold and vetoing only on unanimous "empty" keeps telemetry's recall and lets the VLM remove
the closed-on-nothing runs it can see.

`telem_v4nv` = same thresholds, veto disabled (isolates the effect of the tuned thresholds).
"""
import copy
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import _event_first_lib as lib  # noqa: E402
import event_first_v2 as v2  # noqa: E402
from common import dump_json  # noqa: E402
from telemetry_held import TelemetryCfg, events_from_states, held_runs, held_state_from_telemetry  # noqa: E402

CONFIG = {
    "family": "telemetry_events_vlm_veto",
    "telemetry": asdict(TelemetryCfg(held_lo_m=0.006, held_hi_m=0.034, min_run=8, settle_frames=0, flip_ignore=0)),
    "veto": {"enabled": True, "kind": "veto", "n_frames": 3, "inset": 2, "scale": 2.0, "camera": "both", "temperature": 0.0,
             "unanimous_empty_only": True, "max_runs": 8},
    "identify": copy.deepcopy(v2.CONFIG["identify"]),
    "completion": copy.deepcopy(v2.CONFIG["completion"]),
    "batch": 8,
    "inputs": "observation.state[6] (finger coordinate), action[6] (gripper command), cameras for veto + identity; no priv.*",
}
CONFIG["completion"]["never_held_cause_reaching"] = True


def slot_desc(slot):
    """Glossary description for a slot name like 'black_book_1' (key 'black_book')."""
    from prompt import LIBERO_GLOSSARY

    key = slot.rsplit("_", 1)[0] if slot and slot[-1].isdigit() else slot
    return LIBERO_GLOSSARY.get(key, key.replace("_", " "))


def veto_frames(a, e, n_frames=3, inset=2):
    a2, e2 = min(e, a + inset), max(a, e - inset)
    if n_frames <= 1 or e2 <= a2:
        return [int((a + e) // 2)]
    return sorted({int(round(x)) for x in np.linspace(a2, e2, n_frames)})


def run(ep, backend, workdir, cfg=CONFIG):
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    log = lib.CallLog()
    t0 = time.time()
    tcfg = TelemetryCfg(**cfg["telemetry"])
    states = held_state_from_telemetry(ep.gripper_aperture, ep.gripper_cmd, tcfg)
    runs = held_runs(states)
    glossary = lib.episode_glossary(ep)
    # identification glossary with the exact slot names: the model otherwise answers with the display word ("book"),
    # which cannot be matched to black_book_1 vs yellow_book_1
    id_glossary = chr(10).join(f"- {slot}: {slot_desc(slot)}" for slot in ep.meta.get("object_slots", []))

    vetoes = []
    vc = cfg["veto"]
    if vc.get("enabled") and runs:
        ranked = sorted(runs, key=lambda r: -(r[1] - r[0]))[: int(vc.get("max_runs", 8))]
        plan = {r: veto_frames(r[0], r[1], vc["n_frames"], vc["inset"]) for r in ranked}
        frames = sorted({f for fs in plan.values() for f in fs})
        row_list = lib.run_state_queries(ep, backend, workdir, vc["kind"], frames, scale=vc["scale"], camera=vc["camera"],
                                         temperature=vc["temperature"], repeat=0, batched=True, batch=int(cfg.get("batch", 8)), log=log)
        rows = dict(zip(frames, row_list))  # run_state_queries returns rows in `frames` order (a list)
        for (a, e), fs in plan.items():
            verdicts = []
            for f in fs:
                row = rows.get(f)
                st = None
                if row is not None:
                    parsed = row.get("parsed") or {}
                    sts = parsed.get("states") or []
                    st = sts[0].get("state") if sts else None
                verdicts.append(st or "uncertain")
            n_empty = sum(v == "empty" for v in verdicts)
            vetoed = (n_empty == len(verdicts)) if vc.get("unanimous_empty_only", True) else (n_empty * 2 > len(verdicts))
            vetoes.append({"run": [int(a), int(e)], "frames": [int(f) for f in fs], "verdicts": verdicts, "vetoed": bool(vetoed)})
            if vetoed:
                states[a : e + 1] = "empty"
    runs = held_runs(states)
    raw_events = events_from_states(states, ep.gripper_cmd)

    held_object, idents = None, []
    if runs:
        mids = sorted({int((a + e) // 2) for a, e in runs} | {int(a + (e - a) // 4) for a, e in runs if e - a >= 12} | {int(e - (e - a) // 4) for a, e in runs if e - a >= 12})
        idc = cfg["identify"]
        held_object, idents = lib.identify_held_object(ep, backend, mids, workdir, max_frames=idc["max_frames"], scale=idc["scale"],
                                                       temperature=idc["temperature"], glossary=id_glossary, log=log)

    events = [{"type": e["type"], "object": held_object, "last_before": int(e["last_before"]), "first_after": int(e["first_after"]),
               "chunk": int(ep.chunk_of_frame(int(e["last_before"])))} for e in raw_events]
    n = ep.n_chunks
    prediction = {
        "held_obs": [{"frame": int(i), "state": str(states[i]), "object": None} for i in range(len(states))],
        "events": events, "held_object": held_object,
        "chunk_labels": [None] * n, "chunk_q": [0.0] * n, "decisive_chunk": None, "cause": None,
    }
    evidence = {"telemetry_cfg": asdict(tcfg), "vetoes": vetoes, "held_runs": [[int(a), int(e)] for a, e in runs], "identify": idents}
    v2.complete(ep, cfg, prediction, evidence, [])
    prediction.update(log.as_dict())
    prediction["raw_dir"] = str(workdir)
    prediction["protocol_s"] = round(time.time() - t0, 1)
    dump_json({"config": cfg, "prediction": prediction, "evidence": evidence}, workdir / "result.json")
    return prediction
