"""Print a readable summary of annotation records. Usage: inspect_records.py <tag> [dataset] [--raw]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ANNOT  # noqa: E402

tag = sys.argv[1]
ds = [a for a in sys.argv[2:] if not a.startswith("--")]
raw = "--raw" in sys.argv
root = ANNOT / tag
dirs = [root / d for d in ds] if ds else sorted(p for p in root.iterdir() if p.is_dir())
for d in dirs:
    for p in sorted(d.glob("episode_*.json")):
        r = json.load(open(p))
        a = r.get("annotation") or {}
        g = r.get("gen", {})
        print(f"== {d.name}/{p.name} ok={int(r['success'])} n_chunks={r['n_chunks']} route={r['route']['reasons']} source={r['source']} "
              f"gen_s={g.get('gen_s')} in_tok={g.get('input_tokens')} mem={g.get('max_mem_gb')} wall={r.get('wall_s')}")
        if not a:
            for s in r.get("samples", []):
                print("   FAIL", s.get("error", "")[:160])
            continue
        if r.get("identify"):
            idn = r["identify"]
            for item in idn if isinstance(idn, list) else [idn]:
                print(f"   identify: held={item.get('held')} chunks={item.get('chunks', item.get('chunk'))} parsed={item.get('parsed')}")
        lm = {k: (v.get("value"), v.get("spread")) for k, v in a.get("landmarks", {}).items()}
        print(f"   cause={a.get('cause')} votes={a.get('cause_votes')} landmarks(value,spread)={lm} mean_q={a.get('mean_q')}")
        print(f"   symptom: {a.get('failure_symptom')}")
        print(f"   root:    {a.get('root_cause')}")
        for s in a.get("segments", []):
            print(f"   seg {s['start']:>2}-{s['end']:<2} {s['label']:<17} q={s['confidence']}")
        for s in r.get("samples", []):
            if s["ok"]:
                pj = s["parsed"]
                segs = " ".join(f"{x['start']}-{x['end']}:{x['label'][:4]}" for x in pj["segments"])
                print(f"   sample {s['i']} t*={pj['decisive_error']} onset={pj['failure_onset']} vis={pj['visible_failure']} rec={pj['recoverable_until']} "
                      f"cause={pj['cause']} | {segs}")
                if raw:
                    print("      ", json.dumps(pj)[:600])
            else:
                print(f"   sample {s['i']} PARSE FAIL {s['error'][:120]}")
        if r.get("refine"):
            print(f"   refine window={r['refine']['window']} samples={r['refine']['samples']}")
