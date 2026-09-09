"""Benchmark adapter `whole_p8`: production annotate.py (prompt p8, K=5, identification stage, 1.5x tiles, refinement).

Wraps annotate.run_episode unchanged and maps its record to the normalized prediction of
docs/segmentation_benchmark.md section 3. The method judges no individual frames and emits no events, so
held_obs and events are empty; held_object is the plurality of the identification-stage answers.

Raw cache: the full annotate record is saved to <workdir>/record.json together with a hash of CONFIG; a rerun
with the same config reuses it without calling the model (annotate.py itself has no per-call cache to key on).
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

BENCH_DIR = Path(__file__).resolve().parents[1]
ANNOTATE_DIR = BENCH_DIR.parent
for _p in (str(ANNOTATE_DIR), str(BENCH_DIR)):
    if _p not in sys.path:
        sys.path.append(_p)

from schema import CAUSES, LABELS  # noqa: E402

CONFIG = {
    "model": "Qwen/Qwen3-VL-8B-Instruct",
    "prompt_version": "p8",
    "k": 5,
    "batch": 3,
    "tile_scale": 1.5,
    "temperature": 0.7,
    "max_new_tokens": 1200,
    "max_tiles": 40,
    "refine": True,
    "refine_spread": 2,
    "no_identify": False,
    "include_clean": True,
    "dry_run": False,
    "save_render": False,
    "tag": "bench_whole_p8",
}

_ARG_KEYS = ("model", "k", "batch", "tile_scale", "temperature", "max_new_tokens", "max_tiles", "refine", "refine_spread",
             "no_identify", "include_clean", "dry_run", "save_render")

_MEDIANS = None


def config_hash(cfg):
    return hashlib.sha1(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:12]


def build_args(cfg=CONFIG):
    """argparse-like namespace that annotate.run_episode expects."""
    merged = dict(CONFIG)
    merged.update(cfg or {})
    ns = {k: merged[k] for k in _ARG_KEYS}
    ns.update({"tag": merged.get("tag"), "overwrite": False, "limit": None, "episodes": None, "datasets": None, "failures_only": False})
    return SimpleNamespace(**ns)


def get_medians():
    """(suite, task_id) -> median success length over every finalized dataset; computed once per process."""
    global _MEDIANS
    if _MEDIANS is None:
        from common import list_datasets
        from route import success_length_medians

        _MEDIANS = success_length_medians(list_datasets([]))
    return _MEDIANS


def _most_common_held(identify):
    votes = Counter(i.get("held") for i in (identify or []) if isinstance(i, dict) and i.get("held"))
    if not votes:
        return None
    top = votes.most_common()
    best = [k for k, v in top if v == top[0][1]]
    return sorted(best)[0] if len(best) > 1 else best[0]


def _peak_mem(rec):
    vals = []
    for g in [rec.get("gen"), (rec.get("refine") or {}).get("gen")] + [i.get("gen") for i in rec.get("identify", []) or [] if isinstance(i, dict)]:
        if isinstance(g, dict) and g.get("max_mem_gb") is not None:
            vals.append(float(g["max_mem_gb"]))
    return max(vals) if vals else None


def record_to_prediction(rec, n_chunks=None, workdir=None):
    """annotate.py record -> normalized prediction fields (section 3) that the harness does not fill itself."""
    n = int(rec.get("n_chunks") or n_chunks or 0)
    ann = rec.get("annotation") or None
    labels, q, decisive, cause = [None] * n, [0.0] * n, None, None
    if ann:
        raw_labels = list(ann.get("chunk_label") or [])
        raw_q = list(ann.get("chunk_q") or [])
        for c in range(n):
            lab = raw_labels[c] if c < len(raw_labels) else None
            labels[c] = lab if lab in LABELS else None
            try:
                q[c] = float(raw_q[c]) if c < len(raw_q) and raw_q[c] is not None else 0.0
            except (TypeError, ValueError):
                q[c] = 0.0
        de = ((ann.get("landmarks") or {}).get("decisive_error") or {}).get("value")
        decisive = int(de) if isinstance(de, (int, float)) and not isinstance(de, bool) else None
        c = ann.get("cause")
        cause = c if c in CAUSES else None
    return {
        "held_obs": [],
        "events": [],
        "held_object": _most_common_held(rec.get("identify")),
        "chunk_labels": labels,
        "chunk_q": q,
        "decisive_chunk": decisive,
        "cause": cause,
        "n_chunks": n,
        "source": rec.get("source"),
        "peak_mem_gb": _peak_mem(rec),
        "raw_dir": str(workdir) if workdir is not None else None,
    }


def run(ep, backend, workdir, cfg=CONFIG):
    from annotate import run_episode
    from common import dump_json

    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    h = config_hash(cfg)
    rec_path = workdir / "record.json"
    rec = None
    if rec_path.exists():
        try:
            cached = json.loads(rec_path.read_text())
            if cached.get("bench_config_hash") == h and cached.get("annotation"):
                rec = cached
                rec["reused_cache"] = True
        except (OSError, ValueError):
            rec = None
    if rec is None:
        rec = run_episode(ep, backend, build_args(cfg), get_medians(), cfg.get("tag", CONFIG["tag"]))
        rec["bench_config_hash"] = h
        dump_json(rec, rec_path)
    pred = record_to_prediction(rec, n_chunks=ep.n_chunks, workdir=workdir)
    pred["reused_cache"] = bool(rec.get("reused_cache", False))
    return pred
