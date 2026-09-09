"""oracle_moment: ORACLE-CONDITIONED "describe this moment". Dense frames from the three chunks around the reference
decisive chunk, the verified events and the glossary; the VLM returns the decisive chunk (inside the window), the
cause and one sentence about what the robot did wrong. Chunk labels come from oracle_rules' completion.

Isolates: when the VLM is shown the exact moment of the error with everything it needs to know, can it name the cause
and localise the error to +-1 chunk? When the reference has no decisive chunk (never_reached, held-at-timeout while
moving) the VLM is skipped and the prediction is oracle_rules'. Reads the reference file (including decisive_chunk):
an ablation, never a production annotator.
"""
import copy
import json
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parents[1]):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _event_first_lib as lib  # noqa: E402
import _oracle_lib as olib  # noqa: E402
from render import build_window_tiles, chunk_signals, signals_table  # noqa: E402
from schema import CAUSES, extract_json, norm_cause  # noqa: E402

MOMENT_SYSTEM = """You are an expert reviewer of robot manipulation rollouts. A tabletop episode recorded by a Franka robot in simulation
FAILED, and the moment of the decisive error has already been located to a short window of three action chunks (10 steps,
0.5 s each). You receive:
1. the language instruction the policy was given;
2. a glossary of what the named objects look like;
3. VERIFIED events of the whole episode (when the gripper grasped, dropped or released which object), taken from the
   simulator state: they are correct, do not contradict them;
4. dense frames from the window only, every image labelled with its chunk index and step; the third-person camera is on
   the left, the wrist camera on the right;
5. the robot signals of the window chunks (end-effector position in cm, height change, speed, gripper aperture, command).

Your job is to say WHAT THE ROBOT DID WRONG in this window and in which chunk of the window it did it.
- decisive_chunk: the chunk (one of the window's indices) whose action most determined the failure. It is often EARLIER
  than the visible consequence: an off-centre close precedes the slip, reaching for the wrong object precedes grasping it.
- cause, one of: reaching (never reached / mis-positioned approach), grasp (unstable, off-centre, missed grasp, slip),
  manipulation (wrong placement, rim placement, drop during transport, wrong drawer motion), sequencing_semantic (wrong
  object, wrong order, wrong target region, task misunderstood), collision (arm or gripper hits scene or objects with
  consequences), hardware (never in simulation), other, unclear.
- what_happened: ONE concrete sentence, e.g. "closed the gripper 3 cm left of the can", "released the box on the rim of
  the basket", "reached for the tomato sauce instead of the alphabet soup", "the box slipped out while lifting".
Compare the object between the fingers (wrist view) with the glossary before claiming a wrong object. Output ONLY one
JSON object, no other text:
{"decisive_chunk": <int, one of the window chunk indices>, "cause": "<one of the cause labels>",
 "what_happened": "<one sentence>", "confidence": <0-1>}"""

CONFIG = {
    "family": "oracle_conditioned",
    "oracle_conditioned": True,
    "note": olib.NOTE + " oracle_moment also reads the reference decisive_chunk to cut the window; it asks the VLM only "
                        "for the decisive chunk within that window, the cause and a sentence.",
    "reads_reference_keys": ["events", "held_runs", "target_slot", "decisive_chunk", "n_chunks"],
    "window_chunks": 1, "stride": 2, "tile_scale": 1.5,
    "k": 5, "temperature": 0.5, "max_new_tokens": 300, "batch": 5, "seed": 4400,
    "vote": "plurality over parsed samples; chunk votes outside the window are discarded; ties -> lowest chunk / unclear",
    "mapping": {"decisive_chunk, cause": "VLM vote (null when no sample parsed)", "chunk_labels, chunk_q": "oracle_rules completion",
                "events, held_object": "oracle", "reference decisive null": "no VLM call, oracle_rules prediction"},
    "completion": copy.deepcopy(olib.COMPLETION),
    "expected_calls_per_episode": "1 generate call (k=5); 0 when the reference decisive_chunk is null",
}


def window_for(decisive, n_chunks, half=1):
    return max(0, int(decisive) - half), min(n_chunks - 1, int(decisive) + half)


def build_content(ep, lo, hi, facts_text, cfg=CONFIG):
    glossary = lib.episode_glossary(ep)
    tiles = build_window_tiles(ep, lo, hi, stride=int(cfg["stride"]), scale=float(cfg["tile_scale"]))
    rows = [r for r in chunk_signals(ep) if lo <= r["chunk"] <= hi]
    head = (f"Instruction given to the policy: \"{ep.task}\"\nEpisode outcome: FAILURE. Length: {ep.n} steps = {ep.n_chunks} chunks of 10 steps "
            f"({ep.n / ep.fps:.1f} s at {ep.fps} fps).\n")
    if glossary:
        head += "Objects in this scene:\n" + glossary + "\n"
    head += facts_text + "\n"
    head += f"Window under review: chunks {lo} to {hi} (steps {ep.chunks[lo][0]}-{ep.chunks[hi][1] - 1}). The decisive error happens in this window.\n"
    content = [{"type": "text", "text": head + "\nDense frames from the window:"}]
    for caption, img, _ in tiles:
        content.append({"type": "text", "text": caption + ":"})
        content.append({"type": "image", "image": img})
    content.append({"type": "text", "text": "\nRobot signals for the window chunks (non-privileged):\n" + signals_table(rows)
                    + f"\n\nWhich chunk in {lo}-{hi} holds the decisive error, what is the cause, and what exactly did the robot do wrong? Return the JSON."})
    return content, len(tiles)


def parse_moment(raw, lo, hi):
    """One sample -> {"decisive_chunk": int in window or None, "cause": label, "what_happened": str, "confidence": float, "raw_chunk": ...}."""
    d = json.loads(extract_json(raw))
    if not isinstance(d, dict):
        raise ValueError("top-level JSON is not an object")
    rc = d.get("decisive_chunk")
    chunk = None
    if isinstance(rc, (int, float)) and not isinstance(rc, bool):
        chunk = int(round(float(rc)))
    elif isinstance(rc, str) and rc.strip().lstrip("-").isdigit():
        chunk = int(rc.strip())
    in_window = chunk is not None and lo <= chunk <= hi
    cause = norm_cause(d.get("cause"))
    try:
        conf = max(0.0, min(1.0, float(d.get("confidence", 0.5))))
    except (TypeError, ValueError):
        conf = 0.5
    return {"decisive_chunk": chunk if in_window else None, "raw_chunk": rc, "in_window": in_window, "cause": cause,
            "what_happened": str(d.get("what_happened") or "")[:300], "confidence": conf}


def vote(samples):
    """Plurality for the chunk (in-window votes only; tie -> lowest chunk) and the cause (tie -> unclear)."""
    chunk_votes = Counter(s["decisive_chunk"] for s in samples if s["decisive_chunk"] is not None)
    cause_votes = Counter(s["cause"] for s in samples if s["cause"] in CAUSES)
    decisive = None
    if chunk_votes:
        top = max(chunk_votes.values())
        decisive = min(c for c, n in chunk_votes.items() if n == top)
    cause = None
    if cause_votes:
        ranked = cause_votes.most_common()
        cause = ranked[0][0] if len(ranked) == 1 or ranked[0][1] > ranked[1][1] else "unclear"
    return decisive, cause, {"chunk_votes": {str(k): v for k, v in sorted(chunk_votes.items())}, "cause_votes": dict(cause_votes)}


def run(ep, backend, workdir, cfg=CONFIG, reference=None, ref_dir=None):
    workdir, log, t0, ref, facts, evidence = olib.start(ep, workdir, reference, ref_dir)
    rules_pred, rules_evidence = olib.rules_prediction(ep, facts, cfg["completion"])
    prediction = olib.base_prediction(ep, facts)
    prediction.update({"chunk_labels": rules_pred["chunk_labels"], "chunk_q": rules_pred["chunk_q"], "completion_rules": rules_pred.get("completion_rules")})
    evidence.update({"rules_decisive_cause": [rules_pred["decisive_chunk"], rules_pred["cause"]], "completion": rules_evidence.get("completion")})

    decisive_ref = ref.get("decisive_chunk")
    if decisive_ref is None:
        prediction.update({"decisive_chunk": rules_pred["decisive_chunk"], "cause": rules_pred["cause"]})
        evidence.update({"window": None, "vlm": None, "fallback": "reference decisive_chunk is null: no VLM call, oracle_rules decisive/cause kept"})
        return olib.finish(cfg, prediction, evidence, log, workdir, t0)

    lo, hi = window_for(decisive_ref, ep.n_chunks, int(cfg["window_chunks"]))
    content, n_tiles = build_content(ep, lo, hi, evidence["facts_text"], cfg)
    k = int(cfg["k"])
    row = olib.cached_generate(backend, MOMENT_SYSTEM, content, workdir, "moment", k=k, temperature=float(cfg["temperature"]),
                               max_new_tokens=int(cfg["max_new_tokens"]), batch=int(cfg["batch"]), seed=int(cfg["seed"]), log=log,
                               settings={"window": [lo, hi], "stride": cfg["stride"], "tile_scale": cfg["tile_scale"]})
    samples, errors = [], []
    for raw in row["raws"]:
        try:
            samples.append(parse_moment(raw, lo, hi))
        except Exception as exc:  # noqa: BLE001 - a malformed sample is recorded, not fatal
            errors.append(str(exc)[:200])
    decisive, cause, votes = vote(samples)
    prediction.update({"decisive_chunk": decisive, "cause": cause})
    evidence.update({"window": [lo, hi], "n_tiles": n_tiles,
                     "vlm": {"n_samples": k, "n_parsed": len(samples), "parse_errors": errors, "samples": samples,
                             "sentences": [s["what_happened"] for s in samples], "confidences": [s["confidence"] for s in samples],
                             **votes, "reused_cache": row.get("reused_cache", False)}})
    return olib.finish(cfg, prediction, evidence, log, workdir, t0)
