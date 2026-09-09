"""Pick the benchmark episode sets from the references (docs/segmentation_benchmark.md, section 2).

Reads every reference under $FTL_PROJ/bench/references, keeps failures, drops episodes listed in
scripts/analysis/exclusions.json (any action other than "keep"/"relabel_failure") and episodes whose failure_mode is
"other" (unscorable by construction), then draws
  * bench/episodes.json      50 held-out episodes, stratified by failure_mode (>= MIN_PER_MODE per mode where
                             available, remainder proportional to availability), spread round-robin over
                             (suite, task_id) within each mode, seed 0;
  * bench/episodes_dev.json  20 disjoint episodes for prompt iteration, same procedure (>= 2 per mode).
Usage: select_episodes.py [--datasets fam ...] [--n 50] [--n-dev 20] [--seed 0]
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import PROJ, corrections, dump_json  # noqa: E402
from oracle_reference import MODES, REF_DIR, REFERENCE_VERSION  # noqa: E402

BENCH = REF_DIR.parent
MIN_PER_MODE, MIN_PER_MODE_DEV = 5, 2


def load_references(families):
    refs = []
    for d in sorted(REF_DIR.iterdir()) if REF_DIR.exists() else []:
        if not d.is_dir():
            continue
        if families and not any(d.name == f or d.name.startswith(f + "__t") for f in families):
            continue
        for p in sorted(d.glob("episode_*.json")):
            r = json.loads(p.read_text())
            if r.get("reference_version") != REFERENCE_VERSION:
                print(f"  skipping {p}: reference_version {r.get('reference_version')}")
                continue
            refs.append(r)
    return refs


def excluded(ref):
    for entry in corrections().get(ref["dataset"], []):
        if int(entry["episode_index"]) == int(ref["episode_index"]) and entry["action"] not in ("keep", "relabel_failure"):
            return entry["action"]
    return None


def allocate(avail, total, min_per):
    """Per-mode quota: min(avail, min_per) each, remainder proportional to remaining availability (largest remainder)."""
    modes = [m for m in MODES if avail.get(m, 0) > 0]
    total = min(total, sum(avail[m] for m in modes))
    alloc = {m: min(avail[m], min_per) for m in modes}
    rem = total - sum(alloc.values())
    if rem < 0:  # fewer slots than modes*min_per: trim the largest quotas first, deterministically
        for m in sorted(modes, key=lambda m: (-alloc[m], m)):
            if rem == 0:
                break
            cut = min(alloc[m], -rem)
            alloc[m] -= cut
            rem += cut
    while rem > 0:
        pool = {m: avail[m] - alloc[m] for m in modes if avail[m] > alloc[m]}
        if not pool:
            break
        tot_pool = sum(pool.values())
        shares = {m: rem * pool[m] / tot_pool for m in pool}
        give = {m: min(int(np.floor(shares[m])), pool[m]) for m in pool}
        if sum(give.values()) == 0:  # hand out singles by largest fractional share
            for m in sorted(pool, key=lambda m: (-(shares[m] - np.floor(shares[m])), -pool[m], m)):
                if rem == 0:
                    break
                give[m] = 1
                rem -= 1
            for m, k in give.items():
                alloc[m] += k
            continue
        for m, k in give.items():
            alloc[m] += k
            rem -= k
    return alloc


def pick(candidates, k, rng):
    """k episodes from one mode, round-robin over (suite, task_id) groups, shuffled within groups."""
    groups = defaultdict(list)
    for r in candidates:
        groups[(r["suite"], int(r["task_id"]))].append(r)
    keys = sorted(groups)
    order = [keys[i] for i in rng.permutation(len(keys))]
    for key in keys:
        grp = sorted(groups[key], key=lambda r: (r["dataset"], r["episode_index"]))
        groups[key] = [grp[i] for i in rng.permutation(len(grp))]
    out = []
    while len(out) < k and any(groups[key] for key in order):
        for key in order:
            if groups[key] and len(out) < k:
                out.append(groups[key].pop())
    return out


def select(pool, total, min_per, rng):
    by_mode = defaultdict(list)
    for r in pool:
        by_mode[r["failure_mode"]].append(r)
    alloc = allocate({m: len(v) for m, v in by_mode.items()}, total, min_per)
    chosen = []
    for m in MODES:
        if alloc.get(m, 0):
            chosen += pick(by_mode[m], alloc[m], rng)
    return chosen


def entry(r):
    return {"dataset": r["dataset"], "episode_index": int(r["episode_index"]), "failure_mode": r["failure_mode"],
            "suite": r["suite"], "task_id": int(r["task_id"])}


def table(title, rows, avail):
    print(f"\n== {title} ({len(rows)} episodes)")
    cnt = Counter(r["failure_mode"] for r in rows)
    print(f"  {'mode':18s} {'picked':>6s} {'avail':>6s}  suites/tasks")
    for m in MODES:
        if avail.get(m, 0) or cnt.get(m, 0):
            st = Counter((r["suite"], r["task_id"]) for r in rows if r["failure_mode"] == m)
            print(f"  {m:18s} {cnt.get(m, 0):6d} {avail.get(m, 0):6d}  " + ", ".join(f"{s}/t{t}:{k}" for (s, t), k in sorted(st.items())))
    print("  suites: " + ", ".join(f"{s}={k}" for s, k in sorted(Counter(r["suite"] for r in rows).items())))
    print("  families: " + ", ".join(f"{s}={k}" for s, k in sorted(Counter(r["dataset"].split("__t")[0] for r in rows).items())))
    print(f"  distinct tasks: {len({(r['suite'], r['task_id']) for r in rows})}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datasets", nargs="*", default=[], help="restrict to these dataset families (default: all references)")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--n-dev", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    refs = load_references(args.datasets)
    fails = [r for r in refs if not r["success"]]
    print(f"references: {len(refs)} ({len(fails)} failures)")
    kept, dropped = [], Counter()
    for r in fails:
        why = excluded(r)
        if why:
            dropped[f"exclusions.json:{why}"] += 1
        elif r["failure_mode"] == "other":
            dropped["failure_mode=other"] += 1
        else:
            kept.append(r)
    print("dropped: " + (", ".join(f"{k}={v}" for k, v in dropped.items()) or "none"))
    avail = Counter(r["failure_mode"] for r in kept)
    rng = np.random.default_rng(args.seed)
    held = select(kept, args.n, MIN_PER_MODE, rng)
    held_keys = {(r["dataset"], r["episode_index"]) for r in held}
    rest = [r for r in kept if (r["dataset"], r["episode_index"]) not in held_keys]
    dev = select(rest, args.n_dev, MIN_PER_MODE_DEV, rng)
    assert not held_keys & {(r["dataset"], r["episode_index"]) for r in dev}
    key = lambda r: (MODES.index(r["failure_mode"]), r["dataset"], r["episode_index"])  # noqa: E731
    held, dev = sorted(held, key=key), sorted(dev, key=key)
    dump_json({"reference_version": REFERENCE_VERSION, "seed": args.seed, "episodes": [entry(r) for r in held]}, BENCH / "episodes.json")
    dump_json({"reference_version": REFERENCE_VERSION, "seed": args.seed, "episodes": [entry(r) for r in dev]}, BENCH / "episodes_dev.json")
    table("held-out bench/episodes.json", held, avail)
    table("dev bench/episodes_dev.json", dev, Counter(r["failure_mode"] for r in rest))
    print(f"\nwrote {BENCH / 'episodes.json'} and {BENCH / 'episodes_dev.json'}")


if __name__ == "__main__":
    main()
