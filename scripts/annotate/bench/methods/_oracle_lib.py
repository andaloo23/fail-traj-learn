"""Shared helpers for the ORACLE-CONDITIONED ablation methods (oracle_rules, oracle_whole, oracle_chunk, oracle_moment).

These methods READ THE REFERENCE FILE (bench/references/<dataset>/episode_XXXXXX.json, built from priv.* columns)
and hand the VLM the correct grasp/drop/release events and the correct held object. Their purpose is to isolate the
VLM's SEMANTIC ability (chunk labels, decisive chunk, cause) from its perception (held/empty, identity), which the
production adapters have to get right on their own. They are ablations and must never be used as annotators: every
CONFIG carries "oracle_conditioned": True and the scoreboard should list them separately.

Only the reference keys events / held_runs / target_slot / decisive_chunk / n_chunks are read here; the reference
chunk_labels and cause are never handed to a method (they are the answers).
"""
import copy
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parents[1]):  # bench/methods and scripts/annotate
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _event_first_lib as lib  # noqa: E402
import event_first_v2 as v2  # noqa: E402
from common import PROJ, dump_json  # noqa: E402

REF_DIR = Path(PROJ) / "bench" / "references"
EVENT_TYPES = ("grasp", "release", "drop")
NOTE = ("ORACLE-CONDITIONED ABLATION: this method reads the reference file (privileged simulator state) for the events and "
        "the held object and only asks the VLM the semantic questions. It measures the VLM's semantics given perfect "
        "perception; it is never a production annotator and its predictions must not be used as training labels.")

# reference completion config shared by every oracle method (event_first_v2 rules + reaching for never-held episodes)
COMPLETION = copy.deepcopy(v2.CONFIG["completion"])
COMPLETION["never_held_cause_reaching"] = True


def reference_path(ep, ref_dir=None):
    return Path(ref_dir or REF_DIR) / str(ep.name) / f"episode_{int(ep.ep):06d}.json"


def load_reference(ep, ref_dir=None):
    """The reference record for `ep` (docs/segmentation_benchmark.md section 1)."""
    path = reference_path(ep, ref_dir)
    if not path.exists():
        raise FileNotFoundError(f"oracle-conditioned method needs the reference file {path} (run oracle_reference.py first)")
    ref = json.loads(path.read_text())
    if int(ref.get("n_chunks", ep.n_chunks)) != int(ep.n_chunks):
        raise ValueError(f"reference {path} has {ref.get('n_chunks')} chunks, episode has {ep.n_chunks}")
    return ref


# ----------------------------------------------------------------------------------------------------------------
# facts handed to the methods
# ----------------------------------------------------------------------------------------------------------------
def longest_held_object(held_runs):
    """Object of the longest reference held run (score.py held_object level), None when nothing was held."""
    best, best_len = None, -1
    for r in held_runs or []:
        if r.get("state") != "held":
            continue
        length = int(r["end"]) - int(r["start"]) + 1
        if length > best_len:
            best, best_len = r.get("object"), length
    return best


def oracle_facts(ref):
    """{"events": [{type, last_before, first_after, chunk, object}], "held_object": slot or None} from the reference."""
    events = []
    for e in ref.get("events", []):
        if e.get("type") not in EVENT_TYPES:
            continue
        events.append({"type": str(e["type"]), "last_before": int(e["last_before"]), "first_after": int(e["first_after"]),
                       "chunk": int(e["chunk"]), "object": e.get("object")})
    events.sort(key=lambda e: (e["first_after"], e["last_before"]))
    return {"events": events, "held_object": longest_held_object(ref.get("held_runs", []))}


def _plain(name):
    return str(name).replace("_", " ") if name else "an object"


def facts_text(ref, ep):
    """One short paragraph in plain words stating the verified events and the held object, for the prompts."""
    facts = oracle_facts(ref)
    events, held_object = facts["events"], facts["held_object"]
    target = ref.get("target_slot") or (list(ep.meta.get("target_objects", [])) or [None])[0]
    n_chunks = int(ref.get("n_chunks", ep.n_chunks))
    parts = []
    named = set()
    for e in events:
        obj = e.get("object")
        what = e["type"]
        if obj and obj not in named:
            what += f" of {_plain(obj)}"
            named.add(obj)
        parts.append(f"{what} in chunk {e['chunk']} (steps {e['last_before']}-{e['first_after']})")
    if parts:
        text = "Verified events: " + "; ".join(parts) + "."
    else:
        text = "Verified events: none. The gripper never holds any object during the episode."
    if events:
        last = events[-1]
        if last["type"] == "grasp":
            text += f" The gripper holds {_plain(last.get('object') or held_object)} from chunk {last['chunk']} to the end of the episode (chunk {n_chunks - 1})."
        else:
            text += f" The gripper never holds anything after chunk {last['chunk']}."
    if held_object is not None:
        role = "the target" if target is None or held_object == target else "NOT the target"
        text += f" Object held: {held_object} ({role})."
    else:
        text += " Object held: none."
    return text


def reference_states_rows(ref, n_frames):
    """Per-frame held/empty states from the reference held_runs, in the scan-row format consumed by
    combine_local_evidence.consensus_frames / transitions (like telem_v3.telemetry_states_rows). ambiguous -> uncertain;
    frames not covered by any run -> uncertain."""
    states = ["uncertain"] * int(n_frames)
    for r in ref.get("held_runs", []):
        st = {"held": "held", "empty": "empty"}.get(r.get("state"), "uncertain")
        for f in range(max(0, int(r["start"])), min(int(n_frames) - 1, int(r["end"])) + 1):
            states[f] = st
    return [{"parsed": {"states": [{"frame": int(i), "state": states[i]} for i in range(int(n_frames))]}}]


def base_prediction(ep, facts):
    """The section-3 contract with the oracle's events and held object filled in and every semantic field open."""
    n = ep.n_chunks
    events = [{"type": e["type"], "object": e.get("object"), "last_before": int(e["last_before"]), "first_after": int(e["first_after"]),
               "chunk": int(e["chunk"]) if e.get("chunk") is not None else int(ep.chunk_of_frame(int(e["last_before"])))}
              for e in facts["events"]]
    return {"held_obs": [], "events": events, "held_object": facts["held_object"],
            "chunk_labels": [None] * n, "chunk_q": [0.0] * n, "decisive_chunk": None, "cause": None}


def rules_prediction(ep, facts, completion=None):
    """oracle_rules in one call: base_prediction + event_first_v2.complete with no VLM passes -> (prediction, evidence)."""
    cfg = {"completion": copy.deepcopy(completion if completion is not None else COMPLETION)}
    prediction = base_prediction(ep, facts)
    evidence = {}
    v2.complete(ep, cfg, prediction, evidence, [])
    return prediction, evidence


# ----------------------------------------------------------------------------------------------------------------
# cached multi-sample generate (whole-episode and moment prompts)
# ----------------------------------------------------------------------------------------------------------------
def cached_generate(backend, system, content, workdir, kind, *, k, temperature, max_new_tokens, batch, seed, log, settings=None):
    """backend.generate(k samples) cached under workdir/kind/<input hash>.json like the lib's single-image queries."""
    tag = {"kind": kind, "k": k, "temperature": temperature, "seed": seed, "max_new_tokens": max_new_tokens, **(settings or {})}
    digest = lib.input_hash(system, content, json.dumps(tag, sort_keys=True))
    path = lib._cache_path(workdir, kind, digest)
    row = lib._load_cached(path)
    if row is not None and row.get("input_hash") == digest and len(row.get("raws", [])) == k:
        row["reused_cache"] = True
        return row
    lib.seed_backend(backend, seed)
    raws = backend.generate(system, content, k=k, temperature=temperature, max_new_tokens=max_new_tokens, batch=batch)
    log.record(backend, 1)
    if len(raws) != k:
        raise RuntimeError("backend returned a different number of samples than requested")
    row = {"kind": kind, "k": k, "temperature": temperature, "seed": seed, "max_new_tokens": max_new_tokens, "batch": batch,
           "input_hash": digest, "system": system, "text": [b["text"] for b in content if b["type"] == "text"],
           "n_images": sum(1 for b in content if b["type"] == "image"), "raws": list(raws),
           "generation": dict(getattr(backend, "last", {}) or {}), "time": time.time(), "reused_cache": False}
    dump_json(row, path)
    return row


def get_reference(ep, reference=None, ref_dir=None):
    """(reference dict, where it came from): an injected dict (tests) or the file under ref_dir / REF_DIR."""
    if reference is not None:
        return reference, "injected"
    return load_reference(ep, ref_dir), str(reference_path(ep, ref_dir))


def start(ep, workdir, reference=None, ref_dir=None):
    """Common head of every oracle method: workdir, call log, clock, reference, facts, facts paragraph."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    ref, source = get_reference(ep, reference, ref_dir)
    facts = oracle_facts(ref)
    evidence = {"facts": facts, "facts_text": facts_text(ref, ep),
                "reference": {"source": source, "reference_version": ref.get("reference_version"), "failure_mode": ref.get("failure_mode"),
                              "keys_read": ["events", "held_runs", "target_slot", "decisive_chunk", "n_chunks"]}}
    return workdir, lib.CallLog(), time.time(), ref, facts, evidence


def finish(cfg, prediction, evidence, log, workdir, t0):
    """Common tail: call counters, raw_dir, oracle flag, result.json."""
    prediction.update(log.as_dict())
    prediction["raw_dir"] = str(workdir)
    prediction["protocol_s"] = round(time.time() - t0, 1)
    prediction["oracle_conditioned"] = True
    dump_json({"config": cfg, "prediction": prediction, "evidence": evidence}, Path(workdir) / "result.json")
    return prediction
