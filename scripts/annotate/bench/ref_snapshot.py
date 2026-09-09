"""Snapshot the per-episode verdicts of the references on disk, and compare a snapshot with the current references.

  ref_snapshot.py snapshot --out FILE.json [--datasets prefixes]
      {"<dataset>/<episode>": {"version", "success", "failure_mode", "mode_reason", "decisive_chunk", "n_events",
                               "events": [[type, chunk], ...], "n_scorable", "n_chunks"}}
  ref_snapshot.py compare --before FILE.json --out REPORT.md [--datasets prefixes] [--examples 15]
      per-mode transition table (before -> after), decisive_chunk changes, scorable-chunk totals, examples.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJ, list_datasets  # noqa: E402

ROOT = Path(PROJ) / "bench" / "references"


def read_all(names):
    out = {}
    for name in list_datasets(names or []):
        d = ROOT / name
        if not d.exists():
            continue
        for p in sorted(d.glob("episode_*.json")):
            r = json.loads(p.read_text())
            out[f"{name}/{r['episode_index']}"] = {
                "version": r.get("reference_version"), "success": bool(r["success"]), "failure_mode": r["failure_mode"],
                "mode_reason": r.get("mode_reason"), "decisive_chunk": r.get("decisive_chunk"),
                "n_events": len(r.get("events", [])), "events": [[e["type"], e["chunk"]] for e in r.get("events", [])],
                "n_scorable": sum(bool(c.get("scorable", True)) for c in r["chunk_labels"]), "n_chunks": len(r["chunk_labels"]),
                "n_post_slip": len(r.get("post_slip_closure", [])),
                "rules": dict(Counter(c["rule"].split("+")[0] for c in r["chunk_labels"])),
            }
    return out


def compare(before, after, n_examples):
    keys = sorted(set(before) & set(after))
    only_b, only_a = sorted(set(before) - set(after)), sorted(set(after) - set(before))
    vb = Counter(v["version"] for v in before.values())
    va = Counter(v["version"] for v in after.values())
    lines = ["# Reference changes: r2 -> r3", "",
             f"episodes in both: {len(keys)} (before-only {len(only_b)}, after-only {len(only_a)}); versions before {dict(vb)}, after {dict(va)}", ""]
    fails = [k for k in keys if not before[k]["success"] and not after[k]["success"]]
    succ = [k for k in keys if before[k]["success"]]
    mode_ch = [k for k in fails if before[k]["failure_mode"] != after[k]["failure_mode"]]
    dec_ch = [k for k in fails if before[k]["decisive_chunk"] != after[k]["decisive_chunk"]]
    ev_ch = [k for k in keys if before[k]["events"] != after[k]["events"]]
    lines += [f"failure episodes: {len(fails)}; failure_mode changed: {len(mode_ch)}; decisive_chunk changed: {len(dec_ch)}; "
              f"events changed (any episode): {len(ev_ch)} ({sum(1 for k in ev_ch if k in fails)} failures, {sum(1 for k in ev_ch if k in succ)} successes)", ""]
    # transitions
    trans = Counter((before[k]["failure_mode"], after[k]["failure_mode"]) for k in mode_ch)
    lines += ["## failure_mode transitions (failures whose mode changed)", "", "| before | after | n |", "|---|---|---|"]
    for (b, a), n in sorted(trans.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {b} | {a} | {n} |")
    modes_b = Counter(before[k]["failure_mode"] for k in fails)
    modes_a = Counter(after[k]["failure_mode"] for k in fails)
    lines += ["", "## failure_mode counts", "", "| mode | before | after | delta |", "|---|---|---|---|"]
    for m in sorted(set(modes_b) | set(modes_a), key=lambda m: -modes_b.get(m, 0)):
        lines.append(f"| {m} | {modes_b.get(m, 0)} | {modes_a.get(m, 0)} | {modes_a.get(m, 0) - modes_b.get(m, 0):+d} |")
    # decisive changes per mode (after)
    dec_by_mode = Counter(after[k]["failure_mode"] for k in dec_ch)
    kinds = Counter()
    for k in dec_ch:
        b, a = before[k]["decisive_chunk"], after[k]["decisive_chunk"]
        kinds["null -> set" if b is None else ("set -> null" if a is None else ("moved by 1" if abs(a - b) == 1 else "moved by 2+"))] += 1
    lines += ["", "## decisive_chunk changes", "", f"kinds: {dict(kinds)}", "", "| mode (after) | n |", "|---|---|"]
    for m, n in dec_by_mode.most_common():
        lines.append(f"| {m} | {n} |")
    nul_b = sum(before[k]["decisive_chunk"] is None for k in fails)
    nul_a = sum(after[k]["decisive_chunk"] is None for k in fails)
    lines += ["", f"decisive null among failures: before {nul_b}/{len(fails)}, after {nul_a}/{len(fails)}"]
    # scorable chunks
    sb = sum(before[k]["n_scorable"] for k in fails)
    sa = sum(after[k]["n_scorable"] for k in fails)
    tot = sum(after[k]["n_chunks"] for k in fails)
    lines += [f"scorable chunks (failures): before {sb}/{tot}, after {sa}/{tot}",
              f"episodes with post_slip_closure entries (after): {sum(after[k]['n_post_slip'] > 0 for k in keys)}", ""]
    rb, ra = Counter(), Counter()
    for k in fails:
        rb.update(before[k]["rules"]); ra.update(after[k]["rules"])
    lines += ["## chunk rules (failures)", "", "| rule | before | after |", "|---|---|---|"]
    for r in sorted(set(rb) | set(ra), key=lambda r: -(ra.get(r, 0) + rb.get(r, 0))):
        lines.append(f"| {r} | {rb.get(r, 0)} | {ra.get(r, 0)} |")
    # examples: mode changes first, then decisive-only changes
    ex = mode_ch + [k for k in dec_ch if k not in mode_ch]
    lines += ["", f"## examples ({min(n_examples, len(ex))} of {len(ex)} changed failures)", "",
              "| episode | mode before -> after | decisive before -> after | reason after | events before -> after |", "|---|---|---|---|---|"]
    for k in ex[:n_examples]:
        b, a = before[k], after[k]
        evs = lambda v: " ".join(f"{t[0]}{c}" for t, c in v["events"]) or "-"  # noqa: E731
        lines.append(f"| {k} | {b['failure_mode']} -> {a['failure_mode']} | {b['decisive_chunk']} -> {a['decisive_chunk']} | {a['mode_reason']} | {evs(b)} -> {evs(a)} |")
    return "\n".join(lines) + "\n", {"mode_changed": len(mode_ch), "decisive_changed": len(dec_ch), "events_changed": len(ev_ch), "transitions": trans}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot"); s.add_argument("--out", required=True); s.add_argument("--datasets", nargs="*", default=None)
    c = sub.add_parser("compare"); c.add_argument("--before", required=True); c.add_argument("--out", required=True)
    c.add_argument("--datasets", nargs="*", default=None); c.add_argument("--examples", type=int, default=15)
    args = ap.parse_args()
    if args.cmd == "snapshot":
        snap = read_all(args.datasets)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(snap, indent=0, sort_keys=True))
        print(f"{len(snap)} episodes -> {args.out}; versions {dict(Counter(v['version'] for v in snap.values()))}; "
              f"modes {dict(Counter(v['failure_mode'] for v in snap.values()))}")
    else:
        before = json.loads(Path(args.before).read_text())
        after = read_all(args.datasets)
        md, summary = compare(before, after, args.examples)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md)
        print(md)
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
