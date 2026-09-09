"""Audit the success references: print a few episodes per suspicious category with the facts behind their labels.

Usage: success_audit.py --datasets prefix ... [--per-category 4]
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import list_datasets  # noqa: E402
from oracle_reference import REF_DIR  # noqa: E402


def rules_line(ref):
    short = {"advance": "A", "pre_other": "o", "idle": ".", "other_event": "X", "regrasp": "R", "pre_recovering": "r", "place_release": "P",
             "drop_final": "d", "wrong_release": "w", "wrong_contact_brush": "b", "other_release": "x", "post_success": "_"}
    out = []
    for cl in ref["chunk_labels"]:
        base = cl["rule"].split("+")[0]
        out.append(short.get("advance" if base.startswith("advance") else base, "?"))
    return "".join(out)


def describe(ref):
    ev = ", ".join(f"{e['type'][0]}{e['object'][:8]}@{e['last_before']}(c{e['chunk']})" for e in ref["events"])
    cons = ", ".join(f"{c['start']}-{c['end']}(c{c['chunk']})" for c in ref.get("close_on_nothing", []))
    wrong = ", ".join(f"{w['object'][:10]}:{w['start']}-{w['end']}{'G' if w['grasped'] else ''}" for w in ref.get("wrong_object_contacts", []))
    sf = ref["stage_frames"]
    print(f"  {ref['dataset']} ep{ref['episode_index']:3d} [{ref['suite']} t{ref['task_id']}] n={ref['n_frames']} target={ref['target_slot']} "
          f"reason={ref['mode_reason']} D={ref['decisive_chunk']} cause={ref['cause']}")
    print(f"    task: {ref['task']}")
    print(f"    stages: reached={sf['reached']} grasped={sf['grasped']} lifted={sf['lifted']} transported={sf['transported']} placed={sf['placed']}")
    print(f"    events: {ev or '-'}")
    if cons:
        print(f"    close_on_nothing: {cons}")
    if wrong:
        print(f"    wrong contacts: {wrong}")
    if ref.get("fixture_motion"):
        print("    fixture motion: " + ", ".join(f"{m['joint']}:{m['start']}-{m['end']}({m['delta']:+.3f})" for m in ref["fixture_motion"]))
    if ref["anomalies"]:
        print(f"    anomalies: {ref['anomalies']}")
    print(f"    rules: {rules_line(ref)}   (A=advance o=pre_other .=idle X=other_event R=regrasp r=pre_recovering P=place_release d=drop_final w=wrong_release b=brush x=other_release)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", required=True)
    ap.add_argument("--per-category", type=int, default=4)
    args = ap.parse_args()
    refs = []
    for name in list_datasets(args.datasets):
        d = REF_DIR / name
        if d.exists():
            for p in sorted(d.glob("episode_*.json")):
                r = json.loads(p.read_text())
                if r["success"]:
                    refs.append(r)
    print(f"{len(refs)} success references")
    cats = defaultdict(list)
    for r in refs:
        rules = Counter(cl["rule"].split("+")[0] for cl in r["chunk_labels"])
        if r["mode_reason"] == "success_recovered_close_on_nothing":
            cats["recovered_close_on_nothing"].append(r)
        if r["mode_reason"] == "success_recovered_drop":
            cats["recovered_drop"].append(r)
        if r["mode_reason"] == "success_recovered_wrong_grasp":
            cats["recovered_wrong_grasp"].append(r)
        for k in ("drop_final", "other_release", "wrong_release", "wrong_contact_brush", "idle"):
            if rules.get(k):
                cats[k].append(r)
        if not r["events"]:
            cats["no_events"].append(r)
        if r["stage_frames"]["placed"] < 0:
            cats["no_predicate"].append(r)
        if any(a.startswith("ambiguous_frac") for a in r["anomalies"]):
            cats["ambiguous_frac"].append(r)
        if rules.get("pre_other", 0) / max(len(r["chunk_labels"]), 1) > 0.5:
            cats["mostly_pre_other"].append(r)
        if r["decisive_chunk"] is None and rules.get("pre_recovering"):
            cats["pre_recovering_without_error"].append(r)
        if r["decisive_chunk"] is not None and r["decisive_chunk"] > 0 and all(
                cl["rule"].split("+")[0] not in ("regrasp",) for cl in r["chunk_labels"]):
            cats["error_without_regrasp_rule"].append(r)
    # close-on-nothing detail: how far from the target, and how long before the grasp
    con_lead, before_contact = Counter(), 0
    for r in cats["recovered_close_on_nothing"]:
        grasps = [e["first_after"] for e in r["events"] if e["type"] == "grasp"]
        cons = [c for c in r["close_on_nothing"] if c["chunk"] == r["decisive_chunk"]]
        if cons and grasps:
            lead = min((g - cons[0]["start"] for g in grasps if g > cons[0]["start"]), default=-1)
            con_lead["<=20f" if 0 <= lead <= 20 else ("<=60f" if lead <= 60 else ">60f")] += 1
            before_contact += int(r["stage_frames"]["reached"] < 0 or cons[0]["start"] < r["stage_frames"]["reached"])
    print("recovered close-on-nothing: frames from the closure to the next grasp: " + ", ".join(f"{k}={v}" for k, v in sorted(con_lead.items()))
          + f"; closures before the first target contact: {before_contact}")
    print("categories: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(cats.items())))
    for k in sorted(cats):
        print(f"\n== {k} ({len(cats[k])})")
        for r in cats[k][: args.per_category]:
            describe(r)


if __name__ == "__main__":
    main()
