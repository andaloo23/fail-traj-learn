"""Shared paths, corpus definitions and episode bookkeeping for the offline-RL pipeline.

The RL learner consumes the recorded corpus as flat transitions. Everything the learner needs about a
dataset (which episodes, which slots are the target and the receptacle, the outcome) is resolved here so
that the offline builder (`build_dataset.py`) and the closed-loop evaluator (`eval_env.py`) agree.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))
DATA = PROJ / "data"
RL = Path(os.environ.get("FTL_RL", str(PROJ / "rl")))  # built tensors, checkpoints, logs
BENCH = PROJ / "bench"  # oracle label exports live here
WIN_OUT = Path(os.environ.get("FTL_WIN_OUT", "/mnt/c/Users/LocalPC/dev/fail-traj-learn/outputs"))

# The RL benchmark family: libero_object, one suite, 10 tasks, identical episode structure
# (pick the named object, place it in the basket) at four initial-state perturbation levels.
CORPUS = {
    "object": ["full_anchor", "full_shift4", "full_shift8", "full_shift12", "full_shift16"],
    "object_hard": ["full_shift8", "full_shift12", "full_shift16"],
    "goal": ["full_goal", "full_goals8"],
    "all": ["full_anchor", "full_shift4", "full_shift8", "full_shift12", "full_shift16",
            "full_goal", "full_goals8", "full_l10s8", "full_l10s12", "full_l90"],
}

# Init protocol per dataset family, so closed-loop eval reproduces the training distribution.
INIT_PROTOCOL = {
    "full_anchor": ("libero_object", "standard", 0.0, 0.0),
    "full_shift4": ("libero_object", "shifted", 0.04, 30.0),
    "full_shift8": ("libero_object", "shifted", 0.08, 60.0),
    "full_shift12": ("libero_object", "shifted", 0.12, 90.0),
    "full_shift16": ("libero_object", "shifted", 0.16, 90.0),
    "full_goal": ("libero_goal", "standard", 0.0, 0.0),
    "full_goals8": ("libero_goal", "shifted", 0.08, 60.0),
    "full_l10s8": ("libero_10", "shifted", 0.08, 60.0),
    "full_l10s12": ("libero_10", "shifted", 0.12, 90.0),
    "full_l90": ("libero_90", "standard", 0.0, 0.0),
}

# LIBERO goal predicates name regions of a receptacle, not the receptacle body.
REGION_SUFFIXES = ("_contain_region", "_top_region", "_top_side", "_bottom_side", "_region")


def family_of(name: str) -> str:
    """`full_shift8__t3` -> `full_shift8`."""
    return name.split("__t")[0]


def task_id_of(name: str) -> int:
    return int(name.split("__t")[1])


def expand(prefixes) -> list[str]:
    """Dataset names on disk matching a corpus key, a family prefix, or an exact name."""
    out: list[str] = []
    for p in prefixes:
        out.extend(CORPUS.get(p, [p]))
    names = sorted(
        d.name for d in DATA.iterdir()
        if (d / "meta" / "info.json").exists() and (d / "episodes.jsonl").exists()
    )
    keep = [n for n in names if any(n == a or n.startswith(a + "__t") for a in out)]
    if not keep:
        raise SystemExit(f"no datasets under {DATA} match {out}")
    return keep


def _exclusions() -> dict:
    path = Path(__file__).resolve().parents[1] / "analysis" / "exclusions.json"
    return json.loads(path.read_text()) if path.exists() else {}


def corrected_success(name: str, episode_index: int, success: bool) -> bool:
    """Apply the acceptance-audit relabels (scripts/analysis/exclusions.json)."""
    for e in _exclusions().get(name, []):
        if int(e["episode_index"]) == int(episode_index):
            if e["action"] == "relabel_success":
                return True
            if e["action"] == "relabel_failure":
                return False
    return bool(success)


def dropped_episodes(name: str) -> set[int]:
    return {int(e["episode_index"]) for e in _exclusions().get(name, []) if e["action"] == "drop"}


def sidecar(name: str, ep: int) -> dict:
    return json.loads((DATA / name / "sidecar" / f"episode_{ep:06d}.json").read_text())


def resolve_goal_slots(object_slots: list[str], goal_state, target_objects=None) -> tuple[int, int]:
    """(manipulated-object slot, receptacle slot) for the episode; receptacle is -1 when there is none.

    LIBERO goal clauses look like ['in', 'alphabet_soup_1', 'basket_1_contain_region']: argument 1 is the
    object the policy must move, argument 2 names a region of the receptacle body.
    """
    idx = {n: i for i, n in enumerate(object_slots)}

    def match(arg: str) -> int:
        arg = str(arg)
        if arg in idx:
            return idx[arg]
        for suf in REGION_SUFFIXES:
            if arg.endswith(suf) and arg[: -len(suf)] in idx:
                return idx[arg[: -len(suf)]]
        # last resort: longest object name that prefixes the argument
        cands = [n for n in object_slots if arg.startswith(n)]
        return idx[max(cands, key=len)] if cands else -1

    for clause in goal_state or []:
        args = [str(a) for a in clause]
        if len(args) >= 3:
            t, r = match(args[1]), match(args[2])
            if t >= 0:
                return t, r
        elif len(args) == 2:  # unary predicate (open drawer, turnon stove)
            t = match(args[1])
            if t >= 0:
                return t, -1
    for n in target_objects or []:  # sidecar fallback, ordered as LIBERO's obj_of_interest
        if n in idx:
            others = [m for m in (target_objects or []) if m in idx and m != n]
            return idx[n], (idx[others[0]] if others else -1)
    return 0, -1
