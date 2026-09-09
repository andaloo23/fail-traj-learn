"""Print one reference compactly: verdict, events, close-on-nothing / post-slip closures, and the chunk rules.
Usage: ref_events.py <dataset> <episode> [<dataset> <episode> ...]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJ  # noqa: E402

args = sys.argv[1:]
for name, ep in zip(args[::2], args[1::2]):
    p = Path(PROJ) / "bench" / "references" / name / f"episode_{int(ep):06d}.json"
    r = json.loads(p.read_text())
    print(f"== {name} ep{ep} [{r.get('reference_version')}] {r['failure_mode']} ({r['mode_reason']}) cause={r['cause']} decisive={r['decisive_chunk']} n_frames={r['n_frames']}")
    print("  events: " + " / ".join(f"{e['type']} c{e['chunk']} (f{e['last_before']}-{e['first_after']}, {e['hold_frames']}f{', short' if e['hold_frames'] < 8 else ''})" for e in r["events"]))
    print("  close_on_nothing: " + ", ".join(f"c{x['chunk']} f{x['start']}-{x['end']}" for x in r.get("close_on_nothing", [])))
    print("  post_slip_closure: " + ", ".join(f"c{x['chunk']} f{x['start']}-{x['end']} (after drop f{x['after_drop']})" for x in r.get("post_slip_closure", [])))
    print("  held_runs: " + ", ".join(f"{h['start']}-{h['end']}:{h['state'][:3]}" for h in r["held_runs"] if h["state"] != "empty"))
    for cl in r["chunk_labels"]:
        print(f"  c{cl['chunk']:2d} {cl['primary']:16s} {'|'.join(cl['allowed']):60s} {cl['rule']}{'' if cl.get('scorable', True) else '  (unscorable)'}")
