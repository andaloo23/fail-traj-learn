"""Summarize recorded datasets from their episodes.jsonl files: success rate per dataset and per task.

Usage: summarize_datasets.py [name_or_prefix ...]   (default: all under data/)
Per-task datasets named <prefix>__t<k> are grouped under <prefix>.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path("/home/aliu/projects/fail-traj-learn/data")
all_names = sorted(p.name for p in DATA.iterdir() if (p / "episodes.jsonl").exists())
args = sys.argv[1:]
if args:
    selected = [n for n in all_names if any(n == a or n.startswith(a + "__t") for a in args)]
else:
    selected = all_names

groups: dict[str, list[str]] = defaultdict(list)
for n in selected:
    groups[n.split("__t")[0]].append(n)

grand = defaultdict(lambda: [0, 0, 0])  # source -> [n, success, frames]
for name, members in groups.items():
    eps = []
    for m in members:
        f = DATA / m / "episodes.jsonl"
        if f.exists():
            eps += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    if not eps:
        print(f"{name}: no episodes")
        continue
    per_task = defaultdict(lambda: [0, 0, 0])
    for e in eps:
        k = (e["suite"], e["task_id"], e["task_language"])
        per_task[k][0] += 1
        per_task[k][1] += int(e["success"])
        per_task[k][2] += int(e["length"])
        g = grand[f"{name} ({e['source']}, {e['init_mode']})"]
        g[0] += 1
        g[1] += int(e["success"])
        g[2] += int(e["length"])
    n = len(eps)
    s = sum(int(e["success"]) for e in eps)
    print(f"\n=== {name}: {n} episodes, success {s}/{n} = {100 * s / n:.0f}%, mean length {sum(e['length'] for e in eps) / n:.0f} ===")
    for (suite, tid, lang), (cnt, succ, frames) in sorted(per_task.items()):
        print(f"  {suite}[{tid:2d}] {succ:3d}/{cnt:<3d} ({100 * succ / cnt:3.0f}%)  len {frames / cnt:5.0f}  {lang}")

print("\n=== overall ===")
for k, (n, s, fr) in grand.items():
    print(f"  {k:60s} {s:4d}/{n:<4d} = {100 * s / n:3.0f}%   mean len {fr / n:.0f}")
