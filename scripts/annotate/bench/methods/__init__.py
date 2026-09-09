"""Method registry for the segmentation benchmark (docs/segmentation_benchmark.md section 6).

Every method module exposes
    CONFIG = {...}
    def run(ep, backend, workdir, cfg=CONFIG) -> dict   # normalized prediction minus method/dataset/episode_index/wall_s

Modules are imported lazily so a method that is not written yet only fails when it is asked for.
"""
import importlib
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parents[1]
ANNOTATE_DIR = BENCH_DIR.parent

REGISTRY = {
    "whole_p8": "methods.whole_p8",
    "event_first_v1": "methods.event_first_v1",
    "event_first_batched": "methods.event_first_batched",
    "telem_v3": "methods.telem_v3",
    "telem_v3c": "methods.telem_v3c",
    "telem_v4": "methods.telem_v4",
    "telem_v4nv": "methods.telem_v4nv",
    "telem_v4s": "methods.telem_v4s",
    "event_first_v2": "methods.event_first_v2",
    "fused_v4": "methods.fused_v4",
    # ORACLE-CONDITIONED ablations: read the reference (events, held object) and ask the VLM only the semantic questions.
    # Never production annotators; every CONFIG carries "oracle_conditioned": True.
    "oracle_rules": "methods.oracle_rules",
    "oracle_whole": "methods.oracle_whole",
    "oracle_chunk": "methods.oracle_chunk",
    "oracle_moment": "methods.oracle_moment",
}


def _ensure_paths():
    for p in (str(BENCH_DIR), str(ANNOTATE_DIR)):
        if p not in sys.path:
            sys.path.append(p)


def load_method(name):
    """Import and return the adapter module registered under `name` (must expose CONFIG and run)."""
    if name not in REGISTRY:
        raise KeyError(f"unknown method {name!r}; registered: {sorted(REGISTRY)}")
    modpath = REGISTRY[name]
    _ensure_paths()
    try:
        mod = importlib.import_module(modpath)
    except ModuleNotFoundError as e:
        if e.name in (modpath, modpath.rsplit(".", 1)[-1]):
            raise ImportError(f"method {name!r} is registered as module {modpath!r} but "
                              f"{BENCH_DIR / (modpath.replace('.', '/') + '.py')} does not exist (not written yet?)") from e
        raise
    for attr in ("CONFIG", "run"):
        if not hasattr(mod, attr):
            raise ImportError(f"method module {modpath!r} does not define {attr}")
    return mod
