"""How often does the r2 minimum hold length (8 frames) erase a short target hold? A short ambiguous target run that
is NOT adjacent to a held run of the same object (the 2-frame boundary transition frames are adjacent by
construction) is a hold that r2 demoted. Usage: count_short_holds.py [--datasets prefixes]"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJ, list_datasets  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--datasets", nargs="*", default=None)
args = ap.parse_args()
root = Path(PROJ) / "bench" / "references"
n_eps = n_with = 0
by_len, by_mode, examples = Counter(), Counter(), []
for name in list_datasets(args.datasets or []):
    d = root / name
    if not d.exists():
        continue
    for p in sorted(d.glob("episode_*.json")):
        r = json.loads(p.read_text())
        n_eps += 1
        t = r.get("target_slot")
        held = [(h["start"], h["end"]) for h in r["held_runs"] if h["state"] == "held" and h.get("object") == t]
        def adjacent(a, e):
            return any(a - 3 <= he + 1 and e + 3 >= hs - 1 for hs, he in held)
        short = [h for h in r["held_runs"] if h["state"] == "ambiguous" and h.get("object") == t
                 and 3 <= h["end"] - h["start"] + 1 <= 7 and not adjacent(h["start"], h["end"])]
        if short:
            n_with += 1
            by_mode[r["failure_mode"]] += 1
            for h in short:
                by_len[h["end"] - h["start"] + 1] += 1
            if len(examples) < 12:
                examples.append((name, r["episode_index"], r["failure_mode"], [(h["start"], h["end"]) for h in short]))
print(f"episodes: {n_eps}; with an isolated short (3-7 frame) target hold demoted to ambiguous: {n_with} ({n_with / max(n_eps, 1):.1%})")
print("by run length:", dict(sorted(by_len.items())))
print("by failure mode:", dict(by_mode.most_common()))
for e in examples:
    print("  ", e)
