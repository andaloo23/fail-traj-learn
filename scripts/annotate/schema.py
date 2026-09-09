"""Annotation JSON schema (proposal section 4), parsing of raw VLM text, and normalisation to per-chunk labels."""
import json
import re
from typing import Literal, Optional

import numpy as np
from pydantic import BaseModel, Field, ValidationError

LABELS = ["progress", "failure_inducing", "recovery", "neutral", "aftermath"]
CAUSES = ["reaching", "grasp", "manipulation", "sequencing_semantic", "collision", "hardware", "other", "unclear"]
LANDMARKS = ["failure_onset", "decisive_error", "visible_failure", "recoverable_until"]

Label = Literal["progress", "failure_inducing", "recovery", "neutral", "aftermath"]
Cause = Literal["reaching", "grasp", "manipulation", "sequencing_semantic", "collision", "hardware", "other", "unclear"]

_LABEL_ALIASES = {
    "failure-inducing": "failure_inducing", "failure inducing": "failure_inducing", "failing": "failure_inducing",
    "productive": "progress", "post-failure": "aftermath", "post_failure": "aftermath", "postfailure": "aftermath",
    "idle": "neutral", "recover": "recovery",
}
_CAUSE_ALIASES = {
    "sequencing": "sequencing_semantic", "semantic": "sequencing_semantic", "sequencing/semantic": "sequencing_semantic",
    "sequencing-semantic": "sequencing_semantic", "wrong_object": "sequencing_semantic", "wrong object": "sequencing_semantic",
    "reach": "reaching", "grasping": "grasp", "placement": "manipulation", "manipulate": "manipulation",
    "collide": "collision", "none": "unclear", "n/a": "unclear", "unknown": "unclear", "": "unclear",
}


def norm_label(s):
    s = str(s).strip().lower()
    s = _LABEL_ALIASES.get(s, s).replace("-", "_").replace(" ", "_")
    return s if s in LABELS else None


def norm_cause(s):
    if s is None:
        return "unclear"
    s = str(s).strip().lower()
    s = _CAUSE_ALIASES.get(s, s).replace("-", "_").replace(" ", "_").replace("/", "_")
    return s if s in CAUSES else "other"


class Segment(BaseModel):
    start: int
    end: int  # inclusive chunk index
    label: Label
    cause: Optional[Cause] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    note: Optional[str] = None


class Annotation(BaseModel):
    outcome: Literal["success", "failure"]
    failure_symptom: Optional[str] = None
    root_cause: Optional[str] = None
    cause: Cause = "unclear"
    failure_onset: Optional[int] = None
    decisive_error: Optional[int] = None
    visible_failure: Optional[int] = None
    recoverable_until: Optional[int] = None
    segments: list[Segment]


class ParseError(Exception):
    pass


def extract_json(text):
    """Return the first top-level JSON object in a model response (tolerates code fences / prose / <think> blocks)."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if m:
        return m.group(1)
    i = text.find("{")
    j = text.rfind("}")
    if i < 0 or j <= i:
        raise ParseError("no JSON object found")
    return text[i : j + 1]


def _pre_normalise(d, n_chunks):
    """Fix the recurring soft errors before pydantic sees them."""
    d = dict(d)
    d["outcome"] = "success" if str(d.get("outcome", "")).lower().startswith("succ") else "failure"
    d["cause"] = norm_cause(d.get("cause"))
    for k in LANDMARKS:
        v = d.get(k)
        if v is None or (isinstance(v, str) and v.strip().lower() in ("", "null", "none", "n/a")):
            d[k] = None
        else:
            try:
                d[k] = int(np.clip(int(round(float(v))), 0, n_chunks - 1))
            except (TypeError, ValueError):
                d[k] = None
    segs = []
    for s in d.get("segments", []) or []:
        if not isinstance(s, dict):
            continue
        lab = norm_label(s.get("label"))
        if lab is None:
            continue
        try:
            a, b = int(round(float(s.get("start", 0)))), int(round(float(s.get("end", s.get("start", 0)))))
        except (TypeError, ValueError):
            continue
        a, b = int(np.clip(a, 0, n_chunks - 1)), int(np.clip(b, 0, n_chunks - 1))
        if b < a:
            a, b = b, a
        conf = s.get("confidence", 0.5)
        try:
            conf = float(np.clip(float(conf), 0.0, 1.0))
        except (TypeError, ValueError):
            conf = 0.5
        segs.append({"start": a, "end": b, "label": lab, "cause": norm_cause(s["cause"]) if s.get("cause") else None,
                     "confidence": conf, "note": (str(s["note"])[:200] if s.get("note") else None)})
    d["segments"] = segs
    return d


def validate_structure(raw, n_chunks):
    """Reject temporal repairs: coverage, ordering and indices must be explicit."""
    def index(value):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < n_chunks:
            raise ParseError(f"invalid chunk index: {value!r}")
        return value

    if raw.get("outcome") not in ("success", "failure"):
        raise ParseError("outcome must be success or failure")
    for key in LANDMARKS:
        if raw.get(key) is not None:
            index(raw[key])
    end = 0
    segments = raw.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ParseError("segments must be a nonempty list")
    for segment in segments:
        if not isinstance(segment, dict):
            raise ParseError("invalid segment")
        a, b = index(segment.get("start")), index(segment.get("end"))
        if a != end or b < a:
            raise ParseError("segments must cover all chunks in order without gaps or overlaps")
        if norm_label(segment.get("label")) is None:
            raise ParseError("unknown segment label")
        confidence = segment.get("confidence", 0.5)
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ParseError("invalid confidence")
        end = b + 1
    if end != n_chunks:
        raise ParseError("segments do not cover the episode")


def parse_annotation(text, n_chunks):
    """Raw response text -> Annotation. Raises ParseError when unusable (caller may re-sample)."""
    try:
        raw = json.loads(extract_json(text))
    except json.JSONDecodeError as e:
        raise ParseError(f"invalid JSON: {e}") from e
    if not isinstance(raw, dict):
        raise ParseError("top-level JSON is not an object")
    validate_structure(raw, n_chunks)
    d = _pre_normalise(raw, n_chunks)
    if not d["segments"]:
        raise ParseError("no valid segments")
    try:
        return Annotation(**d)
    except ValidationError as e:
        raise ParseError(str(e)[:300]) from e


def chunk_labels(ann, n_chunks):
    """Per-chunk (label, confidence, cause) arrays. Later segments override earlier ones; gaps inherit the previous
    label (or 'neutral' before the first segment)."""
    validate_structure(ann.model_dump(), n_chunks)
    labels = [None] * n_chunks
    conf = np.zeros(n_chunks)
    cause = [None] * n_chunks
    for s in sorted(ann.segments, key=lambda s: (s.start, s.end)):
        for c in range(s.start, s.end + 1):
            labels[c] = s.label
            conf[c] = s.confidence
            cause[c] = s.cause
    prev, prev_c = "neutral", 0.3
    for c in range(n_chunks):
        if labels[c] is None:
            labels[c], conf[c] = prev, prev_c
        else:
            prev, prev_c = labels[c], conf[c]
    return labels, conf, cause


def segments_from_labels(labels, q):
    """Run-length encode per-chunk labels into segments with mean confidence."""
    segs = []
    start = 0
    for c in range(1, len(labels) + 1):
        if c == len(labels) or labels[c] != labels[start]:
            segs.append({"start": start, "end": c - 1, "label": labels[start], "confidence": round(float(np.mean(q[start:c])), 3)})
            start = c
    return segs
