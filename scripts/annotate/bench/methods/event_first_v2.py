"""event_first_v2: event_first_batched plus (A) a deterministic label-completion layer and (B) batched chunk passes.

Everything up to and including the combine_local_evidence cascade is event_first_batched: two single-frame scans and
the dense refinement through backend.generate_many, wrist identification of the held object, two chunk-label passes
(k=3, T=0.3, context 0 / 5) with the held-object fact line, consensus / transitions / agree_events.

(B) The chunk passes go through backend.generate_many: every chunk prompt is replicated k times in one contents list
(seed set once per pass, top_p 0.8, top_k 20, batch 4; the backend halves the batch on OOM). One cache row per chunk
prompt with its k raw samples, keyed by kind/k/temperature/seed/context/scale (+ sampler), so a rerun is free.

(A) After the cascade, every chunk gets a label from the rules in `complete()` (ids stored per chunk as
"completion_rules" in the prediction and in workdir/result.json). Inputs are only: the agreed events, the identified
held object vs the task target (ep.meta["target_objects"][0]), the recorded outcome (a failure; see CONFIG), the
non-privileged telemetry (eef path per chunk, gripper aperture, gripper command) and the pass-0 local labels/events/
support. No priv.* column and no reference file is read.
"""
import copy
import sys
from collections import Counter
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parents[1]):  # bench/methods and scripts/annotate
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _event_first_lib as lib  # noqa: E402
from event_first_batched import CONFIG as _BATCHED  # noqa: E402

SUPPORT_MIN = 2 / 3           # local label / event support needed to trust the VLM
CLOSED_APERTURE_M = 0.008     # fingers closed on nothing (oracle_reference CLOSED_APERTURE)
CLOSE_MIN_FRAMES = 2          # minimum closed-on-nothing run
MOVING_PATH_CM = 2.0          # eef path per chunk that counts as moving
IDLE_SPEED_M = 0.002          # per-frame eef speed / aperture change below which a frame is idle (episode_progress.py)
IDLE_RUN_MIN_CHUNKS = 4       # trailing idle run (path < MOVING_PATH_CM per chunk) that localises a hold/stall
DEFAULT_Q = 0.6

RULES = {
    "1_drop": "chunk containing an agreed drop (loss while the command stays CLOSE > 0.5 over the bracket) -> failure_inducing",
    "2_release_last": "chunk containing an agreed release that is the last event of the (failed) episode -> failure_inducing",
    "3_close_on_nothing": "chunk containing the ONSET of a close-on-nothing run (command > 0, aperture < 0.008 m, no agreed held state, "
                          ">= 2 frames) -> failure_inducing; a persisting closed-empty state is flagged once, at its onset",
    "4_regrasp": "chunk containing an agreed grasp that follows an earlier drop/release/close-on-nothing -> recovery",
    "5_local_specific": "pass-0 label failure_inducing with support >= 2/3 and majority local event in {wrong_object, collision} -> failure_inducing",
    "6_local": "held chunk (between an agreed grasp and the next loss/release, or containing a grasp): pass-0 label if it is "
               "progress/recovery/failure_inducing with support >= 2/3",
    "6_held_default": "held chunk otherwise -> progress",
    "6i_held_idle": "held chunk that is idle on every frame (speed and aperture change < 2 mm/frame) -> neutral",
    "6s_stall_decisive": "held at episode end: first chunk of the trailing idle run (path < 2 cm per chunk, >= 4 chunks) -> failure_inducing",
    "6s_stall_tail": "held at episode end: chunks after the stall onset -> neutral",
    "7_approach": "before the first agreed grasp / close-on-nothing (held object is the target or nothing was held): progress if path >= 2 cm else neutral",
    "7_wrong_approach": "before the first agreed grasp when the identified held object is NOT the target -> failure_inducing",
    "W_wrong_grasp": "identified held object is NOT the target: chunk containing a grasp -> failure_inducing",
    "W_after_wrong_grasp": "identified held object is NOT the target: every other chunk from the wrong grasp on (held, release, tail) -> neutral",
    "8_between": "between a drop/release/close-on-nothing and a later grasp: progress if path >= 2 cm else neutral",
    "9_tail": "after the last drop/release/close-on-nothing with no later grasp -> neutral",
    "10_local": "nothing ever held and no close-on-nothing: pass-0 label where support >= 2/3",
    "10_motion": "nothing ever held and no close-on-nothing, weak local support: progress if path >= 2 cm else neutral",
}

CONFIG = copy.deepcopy(_BATCHED)
CONFIG.update({
    "base": "event_first_batched",
    "backend": "generate_many",
    "decisive": ("wrong held object -> chunk of its first grasp; else by what ended the LAST hold: drop -> its chunk; release -> its chunk; "
                 "held at end -> first chunk of the trailing idle run (>= 4 chunks with path < 2 cm) or null; never held -> first "
                 "close-on-nothing chunk, else first chunk whose local event is wrong_object (support >= 2/3), else null"),
    "cause": ("wrong held object -> sequencing_semantic; last hold ended by a drop -> grasp; by a release -> manipulation; held at end -> "
              "manipulation; never held with close-on-nothing -> grasp; never held with a wrong_object local event -> sequencing_semantic; else null"),
})
CONFIG["chunk"].update({"sampler": "generate_many", "batch": 4, "top_p": 0.8, "top_k": 20, "seed_policy": "once_per_pass",
                        "cache_key": "kind,k,temperature,seed,context,scale,sampler"})
CONFIG["completion"] = {
    "version": "c1",
    "applied_after": "combine_local_evidence cascade (its labels are kept in result.json evidence.cascade_chunk_labels)",
    "assumes_failure": True,
    "uses_recorded_outcome": "ep.success is read when present; the completion layer is skipped when it is True (every benchmark episode is a failure)",
    "inputs": ["agreed events", "identified held object vs meta.target_objects[0]", "ep.eef_xyz path per chunk", "ep.gripper_aperture",
               "ep.gripper_cmd", "pass-0 local label/support/majority event"],
    "support_min": SUPPORT_MIN, "closed_aperture_m": CLOSED_APERTURE_M, "close_min_frames": CLOSE_MIN_FRAMES, "moving_path_cm": MOVING_PATH_CM,
    "idle_speed_m_per_frame": IDLE_SPEED_M, "idle_run_min_chunks": IDLE_RUN_MIN_CHUNKS,
    "priority": ["W_* (wrong held object branch)", "1", "2", "3", "4", "5", "6*", "10*", "7", "8", "9"],
    "rules": RULES,
    "chunk_q": {"1-4, 9, 6s_*, W_wrong_grasp": 1.0, "5, 6_local, 10_local": "local support", "7, 8, 6_held_default, 6i, 10_motion, W_after": DEFAULT_Q},
}


# ----------------------------------------------------------------------------------------------------------------
# telemetry and event geometry (non-privileged)
# ----------------------------------------------------------------------------------------------------------------
def runs_of(mask):
    """[(start, end_inclusive)] of True runs."""
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return out


def chunk_telemetry(ep):
    """Per chunk: eef path (cm), mean gripper command, min aperture (m), moving (path >= 2 cm), idle (every frame idle)."""
    eef = np.asarray(ep.eef_xyz, dtype=float)
    cmd = np.asarray(ep.gripper_cmd, dtype=float)
    ap = np.asarray(ep.gripper_aperture, dtype=float)
    n = ep.n
    speed = np.linalg.norm(np.diff(eef, axis=0), axis=1)  # speed[i]: motion between frame i and i+1
    dgrip = np.abs(np.diff(ap))
    idle = (speed < IDLE_SPEED_M) & (dgrip < IDLE_SPEED_M)
    rows = []
    for c, (a, b) in enumerate(ep.chunks):
        path_cm = float(np.linalg.norm(np.diff(eef[a:min(n, b + 1)], axis=0), axis=1).sum() * 100)
        seg = idle[a:min(b, n - 1)]
        rows.append({"chunk": c, "path_cm": round(path_cm, 3), "cmd_mean": round(float(cmd[a:b].mean()), 3),
                     "aperture_min_m": round(float(ap[a:b].min()), 4), "moving": bool(path_cm >= MOVING_PATH_CM),
                     "idle": bool(seg.size and seg.all())})
    return rows


def held_mask_from_events(n, events):
    """Frames covered by an agreed held state: grasp.first_after .. next loss.last_before (inclusive), or the episode end."""
    mask = np.zeros(n, dtype=bool)
    start = None
    for e in events:
        if e["type"] == "grasp":
            if start is None:
                start = int(e["first_after"])
        elif start is not None:
            mask[start:int(e["last_before"]) + 1] = True
            start = None
    if start is not None:
        mask[start:] = True
    return mask


def close_on_nothing_runs(ep, held):
    """Runs (>= CLOSE_MIN_FRAMES) of command CLOSE with the fingers closed below CLOSED_APERTURE_M and no agreed held state."""
    cmd = np.asarray(ep.gripper_cmd, dtype=float)
    ap = np.asarray(ep.gripper_aperture, dtype=float)
    closed = (cmd > 0) & (ap < CLOSED_APERTURE_M) & (~np.asarray(held, dtype=bool))
    return [{"start": int(s), "end": int(e), "chunk": ep.chunk_of_frame(int(s))} for s, e in runs_of(closed) if e - s + 1 >= CLOSE_MIN_FRAMES]


def local_summary(records):
    """Per chunk: pass-0 majority label and its support, plus the majority local event and its share of the k samples."""
    out = {}
    for r in records:
        parsed = [s["parsed"] for s in r.get("samples", []) if "parsed" in s]
        k = int(r.get("k") or max(len(r.get("samples", [])), 1))
        events = Counter(p.get("event") for p in parsed if p.get("event"))
        event, count = events.most_common(1)[0] if events else (None, 0)
        out[int(r["chunk"])] = {"label": r.get("label", "uncertain"), "support": float(r.get("support") or 0.0),
                                "event": event, "event_support": count / k}
    return out


def trailing_idle_start(tele, after_chunk):
    """First chunk of the trailing run of chunks (all > after_chunk) with path < MOVING_PATH_CM, if the run has >= IDLE_RUN_MIN_CHUNKS."""
    run = []
    for c in range(len(tele) - 1, after_chunk, -1):
        if tele[c]["path_cm"] < MOVING_PATH_CM:
            run.append(c)
        else:
            break
    return min(run) if len(run) >= IDLE_RUN_MIN_CHUNKS else None


# ----------------------------------------------------------------------------------------------------------------
# the completion layer
# ----------------------------------------------------------------------------------------------------------------
def complete(ep, cfg, prediction, evidence, passes):
    """Replace the cascade's chunk labels / decisive / cause with the rule set above (in place)."""
    cascade_labels = list(prediction["chunk_labels"])
    evidence["cascade_chunk_labels"] = cascade_labels
    evidence["cascade_decisive_cause"] = [prediction["decisive_chunk"], prediction["cause"]]
    if bool(getattr(ep, "success", False)):
        evidence["completion"] = {"skipped": "recorded outcome is success; cascade labels kept"}
        return prediction

    events = sorted(prediction["events"], key=lambda e: (int(e["first_after"]), int(e["last_before"])))
    held_object = prediction.get("held_object")
    targets = list(ep.meta.get("target_objects", []))
    target = targets[0] if targets else None
    wrong_object = held_object is not None and target is not None and held_object != target
    tele = chunk_telemetry(ep)
    held = held_mask_from_events(ep.n, events)
    cons = close_on_nothing_runs(ep, held)
    local = local_summary(passes[0]) if passes else {}

    grasps = [e for e in events if e["type"] == "grasp"]
    ever_held = bool(grasps)
    first_grasp_chunk = int(grasps[0]["chunk"]) if grasps else None
    last_event = events[-1] if events else None
    held_at_end = last_event is not None and last_event["type"] == "grasp"
    # error onsets (frame, kind, chunk): drops, releases and close-on-nothing onsets
    errors = sorted([(int(e["last_before"]), e["type"], int(e["chunk"])) for e in events if e["type"] in ("drop", "release")]
                    + [(r["start"], "close_on_nothing", r["chunk"]) for r in cons])
    grasp_onsets = [(int(e["last_before"]), int(e["chunk"])) for e in grasps]
    stall_chunk = trailing_idle_start(tele, int(last_event["chunk"])) if held_at_end else None
    wrong_local_chunks = sorted(c for c, l in local.items() if l["event"] == "wrong_object" and l["event_support"] >= SUPPORT_MIN)

    labels, qs, rules = [], [], []
    for c, (a, b) in enumerate(ep.chunks):
        t = tele[c]
        loc = local.get(c, {"label": "uncertain", "support": 0.0, "event": None, "event_support": 0.0})
        strong = loc["support"] >= SUPPORT_MIN and loc["label"] not in (None, "uncertain")
        drops_c = [e for e in events if e["type"] == "drop" and int(e["chunk"]) == c]
        grasps_c = [e for e in grasps if int(e["chunk"]) == c]
        cons_c = [r for r in cons if r["chunk"] == c]
        release_last_c = last_event is not None and last_event["type"] == "release" and int(last_event["chunk"]) == c
        earlier_err = any(f < a for f, _, _ in errors)
        later_grasp = any(f >= b for f, _ in grasp_onsets)
        held_c = bool(held[a:b].any()) or bool(grasps_c)
        motion_label = "progress" if t["moving"] else "neutral"

        if wrong_object:
            if grasps_c:
                out = ("failure_inducing", 1.0, "W_wrong_grasp")
            elif drops_c:
                out = ("failure_inducing", 1.0, "1_drop")
            elif first_grasp_chunk is not None and c < first_grasp_chunk:
                out = ("failure_inducing", DEFAULT_Q, "7_wrong_approach")
            else:
                out = ("neutral", DEFAULT_Q, "W_after_wrong_grasp")
        elif drops_c:
            out = ("failure_inducing", 1.0, "1_drop")
        elif release_last_c:
            out = ("failure_inducing", 1.0, "2_release_last")
        elif cons_c:
            out = ("failure_inducing", 1.0, "3_close_on_nothing")
        elif grasps_c and any(f < int(grasps_c[0]["last_before"]) for f, _, _ in errors):
            out = ("recovery", 1.0, "4_regrasp")
        elif strong and loc["label"] == "failure_inducing" and loc["event"] in ("wrong_object", "collision"):
            out = ("failure_inducing", loc["support"], "5_local_specific")
        elif held_c:
            if stall_chunk is not None and c == stall_chunk:
                out = ("failure_inducing", 1.0, "6s_stall_decisive")
            elif stall_chunk is not None and c > stall_chunk:
                out = ("neutral", 1.0, "6s_stall_tail")
            elif t["idle"] and not grasps_c:
                out = ("neutral", DEFAULT_Q, "6i_held_idle")
            elif strong and loc["label"] in ("progress", "recovery", "failure_inducing"):
                out = (loc["label"], loc["support"], "6_local")
            else:
                out = ("progress", DEFAULT_Q, "6_held_default")
        elif not ever_held and not cons:
            out = (loc["label"], loc["support"], "10_local") if strong else (motion_label, DEFAULT_Q, "10_motion")
        elif not earlier_err:
            out = (motion_label, DEFAULT_Q, "7_approach")
        elif later_grasp:
            out = (motion_label, DEFAULT_Q, "8_between")
        else:
            out = ("neutral", 1.0, "9_tail")
        labels.append(out[0])
        qs.append(round(float(out[1]), 4))
        rules.append(out[2])

    if wrong_object and grasps:
        decisive, cause, how = first_grasp_chunk, "sequencing_semantic", "wrong_object_grasp"
    elif last_event is not None and last_event["type"] == "drop":
        decisive, cause, how = int(last_event["chunk"]), "grasp", "drop_ends_last_hold"
    elif last_event is not None and last_event["type"] == "release":
        decisive, cause, how = int(last_event["chunk"]), "manipulation", "release_miss"
    elif held_at_end:
        decisive, cause, how = stall_chunk, "manipulation", "held_at_end"
    elif not ever_held and cons:
        decisive, cause, how = cons[0]["chunk"], "grasp", "close_on_nothing_never_held"
    elif not ever_held and wrong_local_chunks:
        decisive, cause, how = wrong_local_chunks[0], "sequencing_semantic", "wrong_object_local_never_held"
    elif not ever_held and cfg["completion"].get("never_held_cause_reaching"):
        decisive, cause, how = None, "reaching", "never_held_no_error_evidence"
    else:
        decisive, cause, how = None, None, "unlocalised"

    prediction.update({"chunk_labels": labels, "chunk_q": qs, "decisive_chunk": decisive, "cause": cause, "completion_rules": rules})
    evidence["completion_rules"] = rules
    evidence["completion"] = {"version": cfg["completion"]["version"], "target": target, "held_object": held_object, "wrong_object": wrong_object,
                              "ever_held": ever_held, "held_at_end": held_at_end, "stall_chunk": stall_chunk, "decisive_how": how,
                              "close_on_nothing": cons, "errors": errors, "grasp_onsets": grasp_onsets, "wrong_local_chunks": wrong_local_chunks,
                              "telemetry": tele, "local": {str(c): v for c, v in sorted(local.items())}}
    return prediction


def run(ep, backend, workdir, cfg=CONFIG):
    return lib.run_protocol(ep, backend, workdir, cfg, batched=True, chunk_batched=True, finalize=complete)
