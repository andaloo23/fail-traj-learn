"""Side-by-side reference vs prediction for one benchmark episode.

  inspect_episode.py <method> <dataset> <episode_index>

(Named inspect_episode.py rather than inspect.py: a bench/inspect.py would shadow the stdlib `inspect` module for
every script run from this directory, since Python puts the script's directory first on sys.path.)

Prints: level results; per-chunk table (frames, allowed set, primary, rule, predicted label, q, reference held
state summary from held_runs, predicted held summary from held_obs); events of both; decisive/cause of both;
paths of the raw dir and of a contact sheet if one exists.
"""
import sys
from collections import Counter
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
ANNOTATE_DIR = BENCH_DIR.parent
for _p in (str(ANNOTATE_DIR), str(BENCH_DIR)):
    if _p not in sys.path:
        sys.path.append(_p)

from common import PROJ, WIN_OUT  # noqa: E402
from score import LEVELS, load_json, prediction_path, ref_frame_states, reference_path, score_episode  # noqa: E402

RAW_DIR = PROJ / "bench" / "raw"


def _summ(counts, n):
    """Counter of state(object) -> 'held(bowl_1) 8/10, amb 2/10'."""
    if not n:
        return "-"
    parts = []
    for key, v in counts.most_common():
        parts.append(f"{key} {v}/{n}")
    return ", ".join(parts)


def ref_chunk_held(ref, a, b):
    states, objects = ref_frame_states(ref)
    cnt = Counter()
    n = 0
    for i in range(a, b):
        if i >= len(states):
            break
        n += 1
        s = states[i]
        key = "amb" if s == "ambiguous" else (f"held({objects[i]})" if s == "held" else "empty")
        cnt[key] += 1
    return _summ(cnt, n)


def pred_chunk_held(pred, a, b):
    obs = [o for o in (pred.get("held_obs") or []) if a <= int(o.get("frame", -1)) < b]
    cnt = Counter()
    for o in obs:
        s = o.get("state")
        key = f"held({o.get('object')})" if s == "held" else str(s)
        cnt[key] += 1
    return _summ(cnt, len(obs))


def find_contact_sheet(dataset, ep, workdir):
    cands = []
    if workdir.exists():
        cands += sorted(workdir.glob("*sheet*.png")) + sorted(workdir.glob("*.png"))
    pd = WIN_OUT / "annot_preview" / dataset
    if pd.exists():
        cands += sorted(pd.glob(f"ep{int(ep):04d}_*sheet.png"))
    return cands[0] if cands else None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 3:
        sys.exit(__doc__)
    method, dataset, ep = argv[0], argv[1], int(argv[2])
    ref = load_json(reference_path(dataset, ep))
    if ref is None:
        sys.exit(f"no reference at {reference_path(dataset, ep)}")
    pred = load_json(prediction_path(method, dataset, ep))
    workdir = RAW_DIR / method / dataset / f"episode_{ep:06d}"
    res = score_episode(ref, pred)

    print(f"== {method} {dataset} ep{ep:04d}   failure_mode={ref.get('failure_mode')}  suite={ref.get('suite')} task={ref.get('task_id')}")
    print(f"   task: {ref.get('task')}")
    print(f"   target={ref.get('target_slot')} goal={ref.get('goal_slot')} n_frames={ref.get('n_frames')} n_chunks={ref.get('n_chunks')}")
    print(f"   episode: {'PASS' if res['pass'] else 'FAIL at ' + str(res['first_fail'])}  {res['detail']}")
    if pred is None:
        print(f"   (no prediction at {prediction_path(method, dataset, ep)})")
        pred = {}
    elif pred.get("error"):
        print(f"   prediction error: {str(pred['error']).splitlines()[0]}")
    print("-- levels")
    for lv in LEVELS:
        r = res["levels"][lv]
        extra = f"  acc={r['accuracy']:.2f}" if r.get("accuracy") is not None else ""
        print(f"   {lv:<13} {r['status']:<5} {r['detail']}{extra}")

    print("-- decisive / cause")
    print(f"   reference : decisive={ref.get('decisive_chunk')} cause={ref.get('cause')} failure_mode={ref.get('failure_mode')}")
    print(f"   prediction: decisive={pred.get('decisive_chunk')} cause={pred.get('cause')} held_object={pred.get('held_object')}")
    lr = [r for r in ref.get("held_runs") or [] if r.get("state") == "held"]
    if lr:
        longest = max(lr, key=lambda r: r["end"] - r["start"] + 1)
        print(f"   reference longest held run: {longest['object']} frames [{longest['start']},{longest['end']}]")

    print("-- events")
    print("   reference:")
    for e in ref.get("events") or []:
        print(f"     {e.get('type'):<8} {str(e.get('object')):<22} [{e.get('last_before')},{e.get('first_after')}] chunk {e.get('chunk')} cmd_open={e.get('gripper_cmd_open')}")
    if not ref.get("events"):
        print("     (none)")
    print("   prediction:")
    for e in pred.get("events") or []:
        print(f"     {str(e.get('type')):<8} {str(e.get('object')):<22} [{e.get('last_before')},{e.get('first_after')}]")
    if not pred.get("events"):
        print("     (none)")

    print("-- chunks")
    chunks = ref.get("chunks") or []
    by_chunk = {int(c["chunk"]): c for c in ref.get("chunk_labels") or []}
    labels = pred.get("chunk_labels") or []
    qs = pred.get("chunk_q") or []
    hdr = f"   {'ch':>3} {'frames':<10} {'allowed':<36} {'primary':<17} {'rule':<14} {'pred':<17} {'q':>5} ok  {'ref held':<34} pred held"
    print(hdr)
    for c, (a, b) in enumerate(chunks):
        rc = by_chunk.get(c, {})
        allowed = "{" + ",".join(rc.get("allowed", [])) + "}"
        lab = labels[c] if c < len(labels) else None
        q = qs[c] if c < len(qs) else None
        scorable = rc.get("rule") not in ("unlocalised",)
        ok = "  " if not scorable else ("ok" if lab in rc.get("allowed", []) else "XX")
        mark = " <- decisive" if ref.get("decisive_chunk") == c else ""
        pmark = " <- pred decisive" if pred.get("decisive_chunk") == c else ""
        print(f"   {c:>3} {f'{a}-{b - 1}':<10} {allowed:<36} {str(rc.get('primary')):<17} {str(rc.get('rule')):<14} {str(lab):<17} "
              f"{('-' if q is None else f'{q:.2f}'):>5} {ok}  {ref_chunk_held(ref, a, b):<34} {pred_chunk_held(pred, a, b)}{mark}{pmark}")

    print("-- paths")
    print(f"   reference : {reference_path(dataset, ep)}")
    print(f"   prediction: {prediction_path(method, dataset, ep)}")
    print(f"   raw dir   : {workdir}{'' if workdir.exists() else '  (missing)'}")
    sheet = find_contact_sheet(dataset, ep, workdir)
    print(f"   sheet     : {sheet if sheet else '(none)'}")


if __name__ == "__main__":
    main()
