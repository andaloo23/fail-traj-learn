"""In-process event-first segmentation (the run_segmentation_loop.py protocol) for the benchmark harness.

Shared by bench/methods/event_first_v1.py and event_first_batched.py. Reuses the lab prompts and evidence code
(segmentation_lab.STATE_SYSTEM / parse_states / content_for, local_segmenter.SYSTEM / validate,
combine_local_evidence.consensus_frames / transitions / agree_events) but runs everything in one process with a
shared backend, caches every model response under the adapter workdir keyed by an input hash, takes chunk and
frame counts from the episode, and builds the glossary from object_slots + fixtures + target_objects.

No priv.* column is ever read here: the only episode attributes used are frame(), fps, n, chunks, n_chunks,
chunk_of_frame(), task, meta[object_slots/fixtures/target_objects], gripper_cmd and eef_xyz.
"""
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

_ANNOTATE_DIR = Path(__file__).resolve().parents[2]  # scripts/annotate
if str(_ANNOTATE_DIR) not in sys.path:
    sys.path.insert(0, str(_ANNOTATE_DIR))

from combine_local_evidence import agree_events, consensus_frames, transitions  # noqa: E402
from common import dump_json  # noqa: E402
from local_segmenter import SYSTEM as CHUNK_SYSTEM  # noqa: E402
from local_segmenter import validate as validate_chunk  # noqa: E402
from prompt import IDENTIFY_SYSTEM, build_identify_content, scene_glossary  # noqa: E402
from render import FONT  # noqa: E402
from schema import extract_json  # noqa: E402
from segmentation_lab import STATE_SYSTEM, content_for, parse_states  # noqa: E402

STATE_MAX_NEW_TOKENS = 2000   # segmentation_lab.py
CHUNK_MAX_NEW_TOKENS = 420    # local_segmenter.py
IDENTIFY_MAX_NEW_TOKENS = 200  # annotate.py
LAB_SEED = 4200               # segmentation_lab.py: torch.manual_seed(4200 + repeat)


# ----------------------------------------------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------------------------------------------
def episode_glossary(ep):
    """Same glossary construction as annotate.py (object_slots + fixtures + target_objects)."""
    meta = ep.meta
    names = list(meta.get("object_slots", [])) + list(meta.get("fixtures", [])) + list(meta.get("target_objects", []))
    return scene_glossary(names)


def scan_frame_set(n_frames, stride, offset):
    """segmentation_lab.py --frame-stride/--offset sampling: every stride-th frame from offset, plus the last frame."""
    if stride < 1 or not 0 <= offset < stride:
        raise ValueError("invalid single-frame sampling configuration")
    return sorted(set(range(offset, n_frames, stride)) | {n_frames - 1})


def scale_images(content, scale):
    if scale != 1:
        for block in content:
            if block["type"] == "image":
                im = block["image"]
                block["image"] = im.resize((int(im.width * scale), int(im.height * scale)), Image.Resampling.LANCZOS)
    return content


def input_hash(system, content, settings=""):
    """sha256 over system + text blocks + image bytes (+ a settings tag so k/temperature/seed/repeat variants differ)."""
    digest = hashlib.sha256(system.encode())
    for b in content:
        digest.update(b["text"].encode() if b["type"] == "text" else b["image"].tobytes())
    digest.update(str(settings).encode())
    return digest.hexdigest()


def seed_backend(backend, value):
    """Seed sampling like the lab scripts (torch.manual_seed); a fake backend may expose manual_seed instead."""
    fn = getattr(backend, "manual_seed", None)
    if fn is not None:
        fn(int(value))
        return
    try:
        import torch
    except ImportError:  # CPU test environments without torch
        return
    torch.manual_seed(int(value))


class CallLog:
    """Counts backend invocations and prompts and tracks peak memory across a run."""

    def __init__(self):
        self.calls = 0
        self.prompts = 0
        self.peak_mem_gb = 0.0
        self.gen_s = 0.0

    def record(self, backend, n_prompts):
        self.calls += 1
        self.prompts += n_prompts
        last = getattr(backend, "last", None) or {}
        self.peak_mem_gb = max(self.peak_mem_gb, float(last.get("max_mem_gb") or 0.0))
        self.gen_s += float(last.get("gen_s") or 0.0)

    def as_dict(self):
        return {"n_model_calls": self.calls, "n_prompts": self.prompts, "peak_mem_gb": round(self.peak_mem_gb, 2), "gen_s": round(self.gen_s, 1)}


# ----------------------------------------------------------------------------------------------------------------
# cached single-image queries (scans, dense refinement)
# ----------------------------------------------------------------------------------------------------------------
def _cache_path(workdir, kind, digest):
    return Path(workdir) / kind / f"{digest}.json"


def _load_cached(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return None
    return None


def run_state_queries(ep, backend, workdir, kind, frames, *, scale, camera, temperature, repeat, batched, batch, log,
                      max_new_tokens=STATE_MAX_NEW_TOKENS):
    """One held/empty/uncertain judgment per frame (segmentation_lab state_<camera> at --scale), cached by input hash.

    Returns lab-style rows: {"frames": [f], "raw", "parsed"|"error", "input_hash", ...}. Uncached frames go through
    backend.generate one at a time (k=1) or, when `batched`, through backend.generate_many as one call.
    """
    queries = []
    for f in frames:
        system, content = content_for(ep, [f], camera, "state")
        scale_images(content, scale)
        settings = {"kind": kind, "temperature": temperature, "repeat": repeat, "scale": scale, "camera": camera, "k": 1}
        queries.append((f, system, content, input_hash(system, content, json.dumps(settings, sort_keys=True))))
    rows, missing = {}, []
    for f, system, content, digest in queries:
        cached = _load_cached(_cache_path(workdir, kind, digest))
        if cached is not None and cached.get("input_hash") == digest:
            rows[f] = cached
        else:
            missing.append((f, system, content, digest))
    if missing:
        seed = LAB_SEED + repeat
        system = missing[0][1]
        if batched:
            seed_backend(backend, seed)
            raws = backend.generate_many(system, [content for _, _, content, _ in missing], temperature=temperature,
                                         max_new_tokens=max_new_tokens, batch=batch)
            log.record(backend, len(missing))
            generation = [dict(getattr(backend, "last", {}) or {})] * len(missing)
        else:
            raws, generation = [], []
            for _, sys_, content, _ in missing:
                seed_backend(backend, seed)
                raws.append(backend.generate(sys_, content, k=1, temperature=temperature, max_new_tokens=max_new_tokens, batch=1)[0])
                log.record(backend, 1)
                generation.append(dict(getattr(backend, "last", {}) or {}))
        if len(raws) != len(missing):
            raise RuntimeError("backend returned a different number of responses than prompts")
        for (f, sys_, content, digest), raw, gen in zip(missing, raws, generation):
            row = {"kind": kind, "config": f"state_{camera}", "frames": [f], "chunk": ep.chunk_of_frame(f), "scale": scale,
                   "temperature": temperature, "repeat": repeat, "seed": seed, "input_hash": digest, "system": sys_,
                   "text": [b["text"] for b in content if b["type"] == "text"], "raw": raw, "generation": gen,
                   "batched": bool(batched), "time": time.time()}
            try:
                row["parsed"] = parse_states(raw, [f])
            except Exception as exc:  # noqa: BLE001 - a malformed answer is recorded, not fatal
                row["error"] = str(exc)
            dump_json(row, _cache_path(workdir, kind, digest))
            rows[f] = row
    return [rows[f] for f in frames]


def scan(ep, backend, offset, scale, workdir, *, stride=5, camera="both", temperature=0.0, batched=False, batch=8, log=None):
    """Independent single-frame scan of the whole episode (segmentation_lab --frame-stride stride --offset offset)."""
    log = log or CallLog()
    frames = scan_frame_set(ep.n, stride, offset)
    return run_state_queries(ep, backend, workdir, f"scan_o{offset}", frames, scale=scale, camera=camera, temperature=temperature,
                             repeat=0, batched=batched, batch=batch, log=log)


def refine_frames(ep, events, before=2, after=3):
    """segmentation_lab --refine-from: every frame from last_before-2 to first_after+2 of each proposed transition."""
    return sorted({f for event in events for f in range(max(0, event["last_before_frame"] - before),
                                                         min(ep.n, event["first_after_frame"] + after))})


def refine(ep, backend, events, workdir, *, scale=2.0, camera="both", repeats=3, temperature=0.3, batched=False, batch=8, log=None):
    """Dense inspection around proposed transitions, `repeats` sampled answers per frame (seed 4200 + repeat)."""
    log = log or CallLog()
    frames = refine_frames(ep, events)
    rows = []
    for repeat in range(repeats):
        rows += run_state_queries(ep, backend, workdir, "refine", frames, scale=scale, camera=camera, temperature=temperature,
                                  repeat=repeat, batched=batched, batch=batch, log=log)
    return rows


# ----------------------------------------------------------------------------------------------------------------
# per-chunk semantic labels (local_segmenter.py)
# ----------------------------------------------------------------------------------------------------------------
def chunk_frames(ep, c, context):
    a, b = ep.chunks[c]
    return sorted({max(0, a - context), a, (a + b) // 2, b - 1, min(ep.n - 1, b), min(ep.n - 1, b + context)})


def chunk_prompt_text(ep, c, glossary, tracked_events, *, motion=True, extra_facts=()):
    """The local_segmenter user text (--motion, --states-tag), with the annotate.py glossary and optional fact lines."""
    a, b = ep.chunks[c]
    task = f"Task: {ep.task}\nObject appearances:\n" + glossary
    command = np.asarray(ep.gripper_cmd[a:b], dtype=float)
    text = (task + f"\nTARGET chunk {c}: actions at frames {a} through {b - 1}.\n"
            f"Gripper command range in chunk: {command.min():.2f} to {command.max():.2f}; +1 close, -1 open.\n"
            "Judge only this target interval. Context images do not change its boundaries.")
    if motion:
        eef = np.asarray(ep.eef_xyz, dtype=float)
        delta = (eef[min(b, ep.n - 1)] - eef[a]) * 100
        distance = float(np.linalg.norm(np.diff(eef[a:min(b + 1, ep.n)], axis=0), axis=1).sum() * 100)
        text += (f"\nMeasured robot motion in the TARGET interval: xyz displacement in cm = {delta.round(2).tolist()}; "
                 f"end-effector path length = {distance:.2f} cm. This measures motion, not whether it is task-progressing. "
                 "Describe this motion consistently with the images; do not call substantial motion stationary.")
    recent = [e for e in tracked_events if e["first_after_frame"] <= a]
    current = [e for e in tracked_events if e["last_before_frame"] < b and e["first_after_frame"] > a]
    estimate = ("held" if recent[-1]["event"] == "grasp" else "empty") if recent else "not established"
    text += (f"\nSeparate visual tracker estimate at interval start: {estimate}. "
             f"Its supported changes overlapping this interval: {json.dumps(current)}. "
             "These are fallible Qwen visual estimates, not simulator facts. They required consecutive frame confirmations; "
             "a loss_or_release is an observed transition, not a claim about root cause. Reconcile with these images.")
    for line in extra_facts:
        text += "\n" + line
    return text


def held_object_fact_line(held_object, target_names):
    if held_object is None:
        return ("Separate wrist close-up identification: no scene object was clearly identified between the fingers. "
                "This is a fallible visual estimate, not a simulator fact.")
    role = "the task target" if held_object in target_names else "NOT the task target"
    return (f"Separate wrist close-up identification: when something is held it appears to be the {held_object.replace('_', ' ')} "
            f"({role}). This is a fallible visual estimate, not a simulator fact.")


def build_chunk_prompt(ep, c, context, glossary, tracked_events, *, scale=2.0, motion=True, extra_facts=()):
    """The local_segmenter prompt for chunk c: (frames, user text, content blocks with 2x agentview|wrist images)."""
    frames = chunk_frames(ep, c, context)
    text = chunk_prompt_text(ep, c, glossary, tracked_events, motion=motion, extra_facts=extra_facts)
    content = [{"type": "text", "text": text}]
    for i in frames:
        ag, wr = ep.frame(i)
        im = Image.fromarray(np.concatenate([ag, wr], axis=1))
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.Resampling.LANCZOS)
        content.extend([{"type": "text", "text": f"Observation frame {i} ({i / ep.fps:.2f}s)"}, {"type": "image", "image": im}])
    return frames, text, content


def finish_chunk_row(row, raws, frames, k):
    """Parse k raw chunk answers into row["samples"] and set the majority label (strict support > 1/2), votes, support."""
    row["samples"] = []
    for response in raws:
        sample = {"raw": response}
        try:
            sample["parsed"] = validate_chunk(response, frames)
        except Exception as exc:  # noqa: BLE001
            sample["error"] = str(exc)
        row["samples"].append(sample)
    votes = Counter(s["parsed"]["label"] for s in row["samples"] if "parsed" in s)
    label, count = votes.most_common(1)[0] if votes else ("uncertain", 0)
    row["label"] = label if count * 2 > k else "uncertain"
    row["votes"] = dict(votes)
    row["support"] = count / k
    return row


def chunk_pass(ep, backend, states_rows, context, seed, k, workdir, *, kind, scale=2.0, temperature=0.3, motion=True,
               extra_facts=(), glossary=None, log=None, max_new_tokens=CHUNK_MAX_NEW_TOKENS):
    """local_segmenter.py over every chunk: k sampled labels per chunk, majority with strict support > 1/2."""
    log = log or CallLog()
    glossary = episode_glossary(ep) if glossary is None else glossary
    tracked_events = transitions(consensus_frames(states_rows))
    records = []
    for c in range(ep.n_chunks):
        a, b = ep.chunks[c]
        frames, text, content = build_chunk_prompt(ep, c, context, glossary, tracked_events, scale=scale, motion=motion, extra_facts=extra_facts)
        digest = input_hash(CHUNK_SYSTEM, content, json.dumps({"kind": kind, "k": k, "temperature": temperature, "seed": seed,
                                                                "context": context, "scale": scale}, sort_keys=True))
        path = _cache_path(workdir, kind, digest)
        row = _load_cached(path)
        if row is None or row.get("input_hash") != digest:
            seed_backend(backend, seed + c)
            raws = backend.generate(CHUNK_SYSTEM, content, k=k, temperature=temperature, max_new_tokens=max_new_tokens, batch=k)
            log.record(backend, 1)
            row = {"kind": kind, "chunk": c, "frame_interval": [a, b], "frames": frames, "context": context, "seed": seed + c, "k": k,
                   "temperature": temperature, "input_hash": digest, "system": CHUNK_SYSTEM, "input_text": text,
                   "generation": dict(getattr(backend, "last", {}) or {}), "samples": [], "time": time.time()}
            finish_chunk_row(row, raws, frames, k)
            dump_json(row, path)
        records.append(row)
    return records


def chunk_pass_many(ep, backend, states_rows, context, seed, k, workdir, *, kind, scale=2.0, temperature=0.3, top_p=0.8, top_k=20,
                    batch=4, motion=True, extra_facts=(), glossary=None, log=None, max_new_tokens=CHUNK_MAX_NEW_TOKENS):
    """chunk_pass through backend.generate_many: every uncached chunk prompt is replicated k times in one contents list
    (independent left-padded batches of `batch`), the seed is set once per pass. Same prompts, same cache layout
    (one row per chunk prompt with the k raw samples); the cache key adds sampler=generate_many because the sampling
    stream differs from the per-chunk seeding of chunk_pass."""
    log = log or CallLog()
    glossary = episode_glossary(ep) if glossary is None else glossary
    tracked_events = transitions(consensus_frames(states_rows))
    rows, missing = {}, []
    for c in range(ep.n_chunks):
        a, b = ep.chunks[c]
        frames, text, content = build_chunk_prompt(ep, c, context, glossary, tracked_events, scale=scale, motion=motion, extra_facts=extra_facts)
        digest = input_hash(CHUNK_SYSTEM, content, json.dumps({"kind": kind, "k": k, "temperature": temperature, "seed": seed, "context": context,
                                                                "scale": scale, "sampler": "generate_many"}, sort_keys=True))
        path = _cache_path(workdir, kind, digest)
        row = _load_cached(path)
        if row is not None and row.get("input_hash") == digest:
            rows[c] = row
        else:
            missing.append((c, a, b, frames, text, content, digest, path))
    if missing:
        seed_backend(backend, seed)
        contents = [m[5] for m in missing for _ in range(k)]  # each chunk prompt k times, in chunk order
        raws = backend.generate_many(CHUNK_SYSTEM, contents, temperature=temperature, top_p=top_p, top_k=top_k,
                                     max_new_tokens=max_new_tokens, batch=batch)
        log.record(backend, len(contents))
        if len(raws) != len(contents):
            raise RuntimeError("backend returned a different number of responses than prompts")
        generation = dict(getattr(backend, "last", {}) or {})
        for i, (c, a, b, frames, text, content, digest, path) in enumerate(missing):
            row = {"kind": kind, "chunk": c, "frame_interval": [a, b], "frames": frames, "context": context, "seed": seed, "k": k,
                   "temperature": temperature, "top_p": top_p, "top_k": top_k, "sampler": "generate_many", "batch": batch,
                   "input_hash": digest, "system": CHUNK_SYSTEM, "input_text": text, "generation": generation, "samples": [], "time": time.time()}
            finish_chunk_row(row, raws[i * k:(i + 1) * k], frames, k)
            dump_json(row, path)
            rows[c] = row
    return [rows[c] for c in range(ep.n_chunks)]


# ----------------------------------------------------------------------------------------------------------------
# held-object identification (annotate.py identification stage, on frames instead of chunks)
# ----------------------------------------------------------------------------------------------------------------
def pick_frames(frames, max_n):
    frames = sorted(frames)
    if len(frames) <= max_n:
        return frames
    idx = np.linspace(0, len(frames) - 1, max_n).round().astype(int)
    return [frames[int(i)] for i in idx]


def wrist_tile(ep, frame, scale=2.0):
    _, wr = ep.frame(frame)
    img = Image.fromarray(wr)
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    cap = f"frame {frame} (chunk {ep.chunk_of_frame(frame)})"
    d.rectangle([0, 0, d.textlength(cap, font=FONT) + 10, 24], fill=(0, 0, 0))
    d.text((5, 2), cap, fill=(255, 255, 0), font=FONT)
    return (cap, img, (ep.chunk_of_frame(frame), ep.chunk_of_frame(frame)))


def match_slot(answer, slots):
    """annotate.py mapping: the answer must name exactly one slot (full name or base name)."""
    ans = str(answer or "").lower().strip().replace(" ", "_")
    if not ans or ans == "null":
        return None
    candidates = [name for name in slots if ans in (name, name.rsplit("_", 1)[0])]
    return candidates[0] if len(candidates) == 1 else None


def identify_held_object(ep, backend, held_frames, workdir, *, max_frames=4, scale=2.0, temperature=0.0, glossary=None, log=None,
                         max_new_tokens=IDENTIFY_MAX_NEW_TOKENS):
    """Greedy wrist close-up identification at up to `max_frames` held frames; majority over matched slot names.

    Returns (slot name or None, list of per-frame identification records).
    """
    log = log or CallLog()
    glossary = episode_glossary(ep) if glossary is None else glossary
    slots = list(ep.meta.get("object_slots", []))
    idents = []
    for f in pick_frames(held_frames, max_frames):
        tile = wrist_tile(ep, f, scale)
        content = build_identify_content(ep.task, glossary, [tile])
        digest = input_hash(IDENTIFY_SYSTEM, content, json.dumps({"kind": "identify", "temperature": temperature, "scale": scale}, sort_keys=True))
        path = _cache_path(workdir, "identify", digest)
        row = _load_cached(path)
        if row is None or row.get("input_hash") != digest:
            raw = backend.generate(IDENTIFY_SYSTEM, content, k=1, temperature=temperature, max_new_tokens=max_new_tokens, batch=1)[0]
            log.record(backend, 1)
            row = {"kind": "identify", "frame": f, "chunk": ep.chunk_of_frame(f), "input_hash": digest, "raw": raw,
                   "generation": dict(getattr(backend, "last", {}) or {}), "time": time.time()}
            try:
                d = json.loads(extract_json(raw))
                row["parsed"] = d
                row["held"] = match_slot(d.get("held_object"), slots)
            except Exception as exc:  # noqa: BLE001
                row["error"] = str(exc)
                row["held"] = None
            dump_json(row, path)
        idents.append(row)
    votes = Counter(r["held"] for r in idents if r.get("held"))
    if not votes:
        return None, idents
    ranked = votes.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None, idents  # tie between two different objects: do not guess
    return ranked[0][0], idents


# ----------------------------------------------------------------------------------------------------------------
# evidence combination (combine_local_evidence.py main(), as a function) and contract mapping
# ----------------------------------------------------------------------------------------------------------------
def combine_chunk_labels(ep, states, events, local, context):
    """The per-chunk rule cascade of combine_local_evidence.main(): local label, context conflict, motion and
    holding-description contradictions, and the loss-plus-close-command failure_inducing rule."""
    result = []
    eef = np.asarray(ep.eef_xyz, dtype=float)
    cmd = np.asarray(ep.gripper_cmd, dtype=float)
    for c, (a, b) in enumerate(ep.chunks):
        prediction = local.get(c, {})
        label = prediction.get("label", "uncertain")
        notes = []
        provenance = "local_vlm"
        if c in context and context[c]["label"] != label:
            notes.append("local_label_changes_with_context")
            label = "uncertain"
        prior_grasp = any(e["event"] == "grasp" and e["first_after_frame"] <= a for e in events)
        path_cm = float(np.linalg.norm(np.diff(eef[a:min(ep.n, b + 1)], axis=0), axis=1).sum() * 100)
        # Do not silently discard a potentially productive approach as neutral solely because nothing is held.
        if label == "neutral" and not prior_grasp and path_cm > 2:
            notes.append("moving_before_grasp_task_alignment_unverified")
            label = "uncertain"
        observations = [(s.get("parsed", {}).get("observation") or "").lower() for s in prediction.get("samples", [])]
        if path_cm > 2 and sum("stationary" in o for o in observations) >= 2:
            notes.append("stationary_description_contradicts_proprioception")
            label = "uncertain"
        # Retain the distinction between a correct label and an unsupported narrative of holding.
        points = [s for s in states if a <= s["frame"] <= b]
        if points and all(s["state"] == "empty" for s in points) and any("holding" in o or "holds" in o for o in observations):
            notes.append("holding_description_contradicts_frame_observations")
            label = "uncertain"
        for event in events:
            before, after = event["last_before_frame"], event["first_after_frame"]
            # Transition actions are bracketed by before .. after-1. Do not assign across chunk boundaries.
            if event["event"] != "loss_or_release" or not (before < b and after > a):
                continue
            if before < a or after > b:
                notes.append("transition_bracket_spans_chunks_needs_refinement")
                label = "uncertain"
                continue
            command = cmd[before:after]
            if len(command) and np.all(command > 0.5):
                label = "failure_inducing"
                provenance = "independent_visual_loss_plus_close_command"
                notes.append("observed_loss_not_causal_root_error")
            else:
                notes.append("release_intent_unresolved")
        result.append({"chunk": c, "label": label, "local_label": prediction.get("label"), "local_support": prediction.get("support", 0.0),
                       "context_label": context.get(c, {}).get("label"), "provenance": provenance, "notes": notes})
    return result


def event_type(ep, event):
    """Contract event type: grasp, or drop when the gripper command stays CLOSE (> 0.5) over the bracket, else release."""
    if event["event"] == "grasp":
        return "grasp"
    cmd = np.asarray(ep.gripper_cmd, dtype=float)[event["last_before_frame"]:event["first_after_frame"]]
    return "drop" if len(cmd) and bool(np.all(cmd > 0.5)) else "release"


def contract_events(ep, agreed, held_object):
    out = []
    for e in agreed:
        out.append({"type": event_type(ep, e), "object": held_object, "last_before": int(e["last_before_frame"]),
                    "first_after": int(e["first_after_frame"]), "chunk": ep.chunk_of_frame(int(e["last_before_frame"])),
                    "refined": bool(e.get("refined", False)), "source_tracks": e.get("source_tracks", [])})
    return out


def decisive_and_cause(events):
    """The honest baseline of the existing protocol: the last agreed drop is decisive (cause grasp); a final
    release means a placement problem (cause manipulation); otherwise nothing is claimed."""
    drops = [e for e in events if e["type"] == "drop"]
    if drops:
        return drops[-1]["chunk"], "grasp"
    if events and events[-1]["type"] == "release":
        return None, "manipulation"
    return None, None


def combine(ep, scan_rows, refine_rows, local_records, context_records, held_object, held_idents=(), extra=None):
    """Combine scan tracks, refinement, two chunk passes and the identification into the normalized prediction."""
    tracks = {tag: consensus_frames(rows) for tag, rows in scan_rows.items()}
    refined_states = consensus_frames(refine_rows)
    states = consensus_frames([r for rows in scan_rows.values() for r in rows] + list(refine_rows))
    agreed = agree_events(tracks, refined_states)
    local = {r["chunk"]: r for r in local_records}
    context = {r["chunk"]: r for r in context_records}
    chunks = combine_chunk_labels(ep, states, agreed, local, context)
    scan_states = consensus_frames([r for rows in scan_rows.values() for r in rows])
    held_obs = [{"frame": int(s["frame"]), "state": s["state"], "object": None} for s in scan_states]
    events = contract_events(ep, agreed, held_object)
    decisive, cause = decisive_and_cause(events)
    chunk_labels = [None if c["label"] == "uncertain" else c["label"] for c in chunks]
    chunk_q = [0.0 if lab is None else float(c.get("local_support") or 0.0) for lab, c in zip(chunk_labels, chunks)]
    prediction = {"held_obs": held_obs, "events": events, "held_object": held_object, "chunk_labels": chunk_labels, "chunk_q": chunk_q,
                  "decisive_chunk": decisive, "cause": cause}
    evidence = {"states": states, "tracks": tracks, "refined_states": refined_states, "agreed_events": agreed, "chunks": chunks,
                "identify": list(held_idents), **(extra or {})}
    return prediction, evidence


def held_frames_from(states, held_object_source="scan"):
    return [int(s["frame"]) for s in states if s["state"] == "held"]


# ----------------------------------------------------------------------------------------------------------------
# the full protocol
# ----------------------------------------------------------------------------------------------------------------
def run_protocol(ep, backend, workdir, cfg, *, batched, chunk_batched=False, finalize=None):
    """Two scans, dense refinement of scan-A transitions, identification, two chunk passes, combination.

    chunk_batched: run the chunk passes through chunk_pass_many (cfg["chunk"] batch/top_p/top_k) instead of chunk_pass.
    finalize(ep, cfg, prediction, evidence, passes): optional hook that may edit prediction/evidence in place before
    result.json is written (event_first_v2 label completion). Defaults reproduce v1/batched exactly.
    """
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    log = CallLog()
    t0 = time.time()
    sc, rf, ch, idc = cfg["scan"], cfg["refine"], cfg["chunk"], cfg["identify"]
    batch = int(cfg.get("batch", 8))
    glossary = episode_glossary(ep)

    scan_rows = {}
    for offset in sc["offsets"]:
        scan_rows[f"scan_o{offset}"] = scan(ep, backend, offset, sc["scale"], workdir, stride=sc["stride"], camera=sc["camera"],
                                            temperature=sc["temperature"], batched=batched, batch=batch, log=log)
    tags = list(scan_rows)
    proposed = transitions(consensus_frames(scan_rows[tags[0]]))  # refinement is driven by scan A, like the loop
    refine_rows = refine(ep, backend, proposed, workdir, scale=rf["scale"], camera=sc["camera"], repeats=rf["repeats"],
                         temperature=rf["temperature"], batched=batched, batch=batch, log=log)

    scan_states = consensus_frames([r for rows in scan_rows.values() for r in rows])
    held_frames = held_frames_from(scan_states)
    held_object, idents = (None, [])
    if held_frames:
        held_object, idents = identify_held_object(ep, backend, held_frames, workdir, max_frames=idc["max_frames"], scale=idc["scale"],
                                                   temperature=idc["temperature"], glossary=glossary, log=log)

    extra_facts = [held_object_fact_line(held_object, list(ep.meta.get("target_objects", [])))] if ch.get("held_object_fact") else []
    passes = []
    for i, p in enumerate(cfg["chunk_passes"]):
        states_rows = scan_rows[tags[p["states"]]]
        if chunk_batched:
            passes.append(chunk_pass_many(ep, backend, states_rows, p["context"], p["seed"], ch["k"], workdir, kind=f"chunk_pass{i}",
                                          scale=ch["scale"], temperature=ch["temperature"], top_p=ch.get("top_p", 0.8), top_k=ch.get("top_k", 20),
                                          batch=int(ch.get("batch", 4)), motion=ch["motion"], extra_facts=extra_facts, glossary=glossary, log=log))
        else:
            passes.append(chunk_pass(ep, backend, states_rows, p["context"], p["seed"], ch["k"], workdir, kind=f"chunk_pass{i}",
                                     scale=ch["scale"], temperature=ch["temperature"], motion=ch["motion"], extra_facts=extra_facts,
                                     glossary=glossary, log=log))

    prediction, evidence = combine(ep, scan_rows, refine_rows, passes[0], passes[1] if len(passes) > 1 else [], held_object, idents,
                                   extra={"held_frames_for_identify": pick_frames(held_frames, idc["max_frames"]),
                                          "refine_frames": refine_frames(ep, proposed), "proposed_from_scan_a": proposed})
    if finalize is not None:
        finalize(ep, cfg, prediction, evidence, passes)
    prediction.update(log.as_dict())
    prediction["raw_dir"] = str(workdir)
    prediction["protocol_s"] = round(time.time() - t0, 1)
    dump_json({"config": cfg, "prediction": prediction, "evidence": evidence}, workdir / "result.json")
    return prediction
