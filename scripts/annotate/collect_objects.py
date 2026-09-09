"""List every object slot / target / fixture name that appears in the corpus (from sidecar episode 0 of each dataset),
so the prompt glossary can cover all of them. Usage: collect_objects.py [prefix ...]"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, list_datasets  # noqa: E402

objs, targets, fixtures, tasks = Counter(), Counter(), Counter(), {}
for name in list_datasets(sys.argv[1:]):
    p = DATA / name / "sidecar" / "episode_000000.json"
    if not p.exists():
        continue
    m = json.load(open(p))
    objs.update(m["object_slots"])
    targets.update(m["target_objects"])
    fixtures.update(m.get("fixtures", []))
    tasks[(m["suite"], m["task_id"])] = m["task_language"]
print("OBJECT SLOTS:", sorted(objs))
print("TARGETS:", sorted(targets))
print("FIXTURES:", sorted(fixtures))
print("TASKS:")
for k in sorted(tasks):
    print(f"  {k[0]}[{k[1]}]: {tasks[k]}")
