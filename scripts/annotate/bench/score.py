"""Score benchmark predictions against oracle references (docs/segmentation_benchmark.md section 4).

  score.py --methods whole_p8 event_first_v1 [--set dev|heldout|all] [--name scoreboard]

Reads   $FTL_PROJ/bench/references/<dataset>/episode_XXXXXX.json
        $FTL_PROJ/bench/predictions/<method>/<dataset>/episode_XXXXXX.json
Writes  outputs/bench/<name>.md and <name>.json (Windows side via common.WIN_OUT).

Levels, in table order (a level is skipped when the reference marks it not applicable). Reference version r2:
scoring is at annotation granularity (10-frame chunks).
  held_state   DIAGNOSTIC (shown, not part of the episode pass): every judged frame whose reference state is not
               ambiguous matches; uncertain = wrong (skipped when the method judged no frames)
  events       every reference event matched one-to-one by a predicted event of the same type whose last_before
               falls in the reference event's chunk +-1 (|chunk(pred.last_before) - ref.chunk| <= EVENT_CHUNK_TOL);
               no unmatched predicted events
  held_object  equals the object of the longest reference held run (skipped when there is none)
  chunk_labels every chunk with a scorable rule (rule != "unlocalised") has its label in the allowed set;
               abstain (null) fails (skipped when no chunk is scorable)
  chunk_labels_1off  DIAGNOSTIC: at most one scorable chunk outside its allowed set
  decisive     |pred - ref| <= 1 (skipped when the reference decisive chunk is null)
  cause        equal
  episode      all applicable OVERALL_LEVELS pass (events, held_object, chunk_labels, decisive, cause)
  semantic     chunk_labels, decisive and cause pass (column in the scoreboard)
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
ANNOTATE_DIR = BENCH_DIR.parent
for _p in (str(ANNOTATE_DIR),):
    if _p not in sys.path:
        sys.path.append(_p)

from common import PROJ, WIN_OUT, dump_json  # noqa: E402

LEVELS = ["held_state", "events", "held_object", "chunk_labels", "chunk_labels_1off", "decisive", "cause"]  # table order
OVERALL_LEVELS = ["events", "held_object", "chunk_labels", "decisive", "cause"]  # the episode pass
DIAGNOSTIC_LEVELS = [lv for lv in LEVELS if lv not in OVERALL_LEVELS]
SEMANTIC_LEVELS = ("chunk_labels", "decisive", "cause")
EVENT_CHUNK_TOL = 1
DECISIVE_TOL = 1
ONE_OFF_MAX_WRONG = 1
UNSCORABLE_RULES = {"unlocalised"}

BENCH = PROJ / "bench"
REF_DIR = BENCH / "references"
PRED_DIR = BENCH / "predictions"


# ------------------------------------------------------------------ paths / loading
def ep_name(ep):
    return f"episode_{int(ep):06d}.json"


def reference_path(dataset, ep):
    return REF_DIR / dataset / ep_name(ep)


def prediction_path(method, dataset, ep):
    return PRED_DIR / method / dataset / ep_name(ep)


def load_json(path):
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_episode_set(which, bench_dir=BENCH):
    """[(dataset, episode_index), ...] for dev | heldout | all, deduplicated, in file order."""
    files = {"dev": ["episodes_dev.json"], "heldout": ["episodes.json"], "all": ["episodes_dev.json", "episodes.json"]}[which]
    out, seen = [], set()
    for f in files:
        p = Path(bench_dir) / f
        if not p.exists():
            raise FileNotFoundError(f"episode set file missing: {p} (run select_episodes.py first)")
        d = json.loads(p.read_text())
        for e in d["episodes"]:
            key = (e["dataset"], int(e["episode_index"]))
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out


# ------------------------------------------------------------------ reference helpers
def ref_frame_states(ref):
    """Per-frame reference held state from held_runs (frames [start, end] inclusive); 'empty' where uncovered."""
    n = int(ref.get("n_frames") or 0)
    runs = ref.get("held_runs") or []
    if runs:
        n = max(n, max(int(r["end"]) for r in runs) + 1)
    states = ["empty"] * n
    objects = [None] * n
    for r in runs:
        for i in range(int(r["start"]), int(r["end"]) + 1):
            if 0 <= i < n:
                states[i] = r["state"]
                objects[i] = r.get("object")
    return states, objects


def longest_held_run(ref):
    runs = [r for r in (ref.get("held_runs") or []) if r.get("state") == "held"]
    if not runs:
        return None
    return max(runs, key=lambda r: (int(r["end"]) - int(r["start"]) + 1, -int(r["start"])))


def scorable_chunks(ref):
    return [c for c in (ref.get("chunk_labels") or []) if c.get("rule") not in UNSCORABLE_RULES]


def chunk_of_frame(ref, frame):
    """Chunk index containing a frame, from the reference's chunk table (clamped to the first/last chunk like the
    oracle's _chunk_of); None when the reference has no chunk table or the frame is not an int."""
    chunks = ref.get("chunks") or []
    try:
        f = int(frame)
    except (TypeError, ValueError):
        return None
    if not chunks:
        return None
    if f < int(chunks[0][0]):
        return 0
    for c, (a, b) in enumerate(chunks):
        if int(a) <= f < int(b):
            return c
    return len(chunks) - 1


def _res(status, detail="", **extra):
    d = {"status": status, "detail": detail}
    d.update(extra)
    return d


# ------------------------------------------------------------------ levels
def score_held_state(ref, pred):
    obs = pred.get("held_obs") or []
    if not obs:
        return _res("skip", "no frames judged", accuracy=None, n_judged=0)
    states, _ = ref_frame_states(ref)
    n_checked = n_ok = 0
    first_bad = None
    for o in obs:
        f = int(o["frame"])
        r = states[f] if 0 <= f < len(states) else None
        if r is None:
            if first_bad is None:
                first_bad = f"frame {f} outside reference range"
            n_checked += 1
            continue
        if r == "ambiguous":
            continue
        n_checked += 1
        if o.get("state") == r:
            n_ok += 1
        elif first_bad is None:
            first_bad = f"frame {f} predicted {o.get('state')}, ref {r}"
    acc = (n_ok / n_checked) if n_checked else 1.0
    if n_checked == n_ok:
        return _res("pass", f"{n_ok}/{n_checked} judged frames correct", accuracy=acc, n_judged=len(obs))
    return _res("fail", f"{first_bad} ({n_checked - n_ok}/{n_checked} wrong)", accuracy=acc, n_judged=len(obs))


def _max_matching(adj, n_right):
    """Maximum bipartite matching (Kuhn). adj[i] = right nodes compatible with left node i. -> match_right list
    (right j -> left i or None). Sizes here are a handful of events, so the O(V*E) DFS is fine."""
    match_right = [None] * n_right

    def augment(i, seen):
        for j in adj[i]:
            if j in seen:
                continue
            seen.add(j)
            if match_right[j] is None or augment(match_right[j], seen):
                match_right[j] = i
                return True
        return False

    for i in range(len(adj)):
        augment(i, set())
    return match_right


def score_events(ref, pred):
    """Chunk-granularity one-to-one matching: a predicted event of the same type matches a reference event when the
    chunk of its last_before is within EVENT_CHUNK_TOL of the reference event's chunk (= chunk of ref.last_before).
    Every reference event must be matched and no predicted event may be left over."""
    refs = list(ref.get("events") or [])
    preds = list(pred.get("events") or [])
    ref_chunks = [int(r["chunk"]) if r.get("chunk") is not None else chunk_of_frame(ref, r.get("last_before")) for r in refs]
    pred_chunks = [chunk_of_frame(ref, p.get("last_before")) for p in preds]
    adj = []
    for r, rc in zip(refs, ref_chunks):
        adj.append([j for j, (p, pc) in enumerate(zip(preds, pred_chunks))
                    if p.get("type") == r.get("type") and rc is not None and pc is not None and abs(pc - rc) <= EVENT_CHUNK_TOL])
    match_right = _max_matching(adj, len(preds))
    matched_left = {i for i in match_right if i is not None}
    missing = [(r, rc) for i, (r, rc) in enumerate(zip(refs, ref_chunks)) if i not in matched_left]
    unmatched = [(p, pc) for j, (p, pc) in enumerate(zip(preds, pred_chunks)) if match_right[j] is None]
    n_ok = len(refs) - len(missing)
    if not missing and not unmatched:
        return _res("pass", f"{len(refs)} reference events matched, {len(preds)} predicted", n_ref=len(refs), n_pred=len(preds), n_matched=n_ok)
    parts = []
    if missing:
        r, rc = missing[0]
        parts.append(f"ref {r.get('type')} chunk {rc} [{r.get('last_before')},{r.get('first_after')}] unmatched" + (f" (+{len(missing) - 1} more)" if len(missing) > 1 else ""))
    if unmatched:
        p, pc = unmatched[0]
        parts.append(f"predicted {p.get('type')} chunk {pc} [{p.get('last_before')},{p.get('first_after')}] matches nothing" + (f" (+{len(unmatched) - 1} more)" if len(unmatched) > 1 else ""))
    return _res("fail", "; ".join(parts), n_ref=len(refs), n_pred=len(preds), n_matched=n_ok)


def score_held_object(ref, pred):
    run = longest_held_run(ref)
    if run is None:
        return _res("skip", "reference has no held run")
    want = run.get("object")
    got = pred.get("held_object")
    if got == want:
        return _res("pass", f"held_object {want}")
    return _res("fail", f"held_object {got} vs ref {want}")


def _chunk_label_errors(ref, pred):
    """-> (scorable chunks, [(chunk index, message)] for every scorable chunk whose label is outside its allowed set)."""
    scor = scorable_chunks(ref)
    labels = list(pred.get("chunk_labels") or [])
    bad = []
    for c in scor:
        i = int(c["chunk"])
        lab = labels[i] if i < len(labels) else None
        if lab is None or lab not in c["allowed"]:
            allowed = "{" + ",".join(c["allowed"]) + "}"
            bad.append((i, f"chunk {i} {'abstained' if lab is None else 'predicted ' + str(lab)}, allowed {allowed}"))
    return scor, bad


def score_chunk_labels(ref, pred):
    scor, bad = _chunk_label_errors(ref, pred)
    if not scor:
        return _res("skip", "no scorable chunk (unlocalised)", accuracy=None)
    n_ok = len(scor) - len(bad)
    acc = n_ok / len(scor)
    if not bad:
        return _res("pass", f"{n_ok}/{len(scor)} scorable chunks correct", accuracy=acc)
    return _res("fail", f"{bad[0][1]} ({len(bad)}/{len(scor)} wrong)", accuracy=acc)


def score_chunk_labels_1off(ref, pred):
    """Diagnostic: pass when at most ONE_OFF_MAX_WRONG scorable chunks are outside their allowed set."""
    scor, bad = _chunk_label_errors(ref, pred)
    if not scor:
        return _res("skip", "no scorable chunk (unlocalised)", n_wrong=None)
    if len(bad) <= ONE_OFF_MAX_WRONG:
        return _res("pass", f"{len(bad)}/{len(scor)} scorable chunks wrong", n_wrong=len(bad))
    return _res("fail", f"{len(bad)}/{len(scor)} scorable chunks wrong (first: {bad[0][1]})", n_wrong=len(bad))


def score_decisive(ref, pred):
    r = ref.get("decisive_chunk")
    if r is None:
        return _res("skip", "reference decisive null")
    p = pred.get("decisive_chunk")
    if p is None:
        return _res("fail", f"decisive null vs ref {r}")
    if abs(int(p) - int(r)) <= DECISIVE_TOL:
        return _res("pass", f"decisive {p} vs ref {r}")
    return _res("fail", f"decisive {p} vs ref {r}")


def score_cause(ref, pred):
    r, p = ref.get("cause"), pred.get("cause")
    if p == r:
        return _res("pass", f"cause {r}")
    return _res("fail", f"cause {p} vs ref {r}")


LEVEL_FN = {
    "held_state": score_held_state,
    "events": score_events,
    "held_object": score_held_object,
    "chunk_labels": score_chunk_labels,
    "chunk_labels_1off": score_chunk_labels_1off,
    "decisive": score_decisive,
    "cause": score_cause,
}


def _applicable_levels(ref):
    out = {}
    out["held_state"] = True
    out["events"] = True
    out["held_object"] = longest_held_run(ref) is not None
    out["chunk_labels"] = bool(scorable_chunks(ref))
    out["chunk_labels_1off"] = out["chunk_labels"]
    out["decisive"] = ref.get("decisive_chunk") is not None
    out["cause"] = True
    return out


def score_episode(ref, pred):
    """Per-level results + episode aggregate for one (reference, prediction). pred=None = missing prediction.
    The episode passes when every applicable level in OVERALL_LEVELS passes; DIAGNOSTIC_LEVELS are computed and
    reported but never fail the episode (first_fail is over OVERALL_LEVELS)."""
    levels = {}
    if pred is None:
        app = _applicable_levels(ref)
        for lv in LEVELS:
            levels[lv] = _res("fail", "missing prediction") if app[lv] else _res("skip", "not applicable")
        return {"levels": levels, "pass": False, "first_fail": "missing", "detail": "missing prediction", "error": None}
    for lv in LEVELS:
        try:
            levels[lv] = LEVEL_FN[lv](ref, pred)
        except Exception as e:  # noqa: BLE001 - a malformed prediction must not stop the scoreboard
            levels[lv] = _res("fail", f"scorer error: {type(e).__name__}: {e}")
    fails = [lv for lv in OVERALL_LEVELS if levels[lv]["status"] == "fail"]
    err = pred.get("error")
    if err:
        return {"levels": levels, "pass": False, "first_fail": "error", "detail": str(err).splitlines()[0][:160] if str(err).strip() else "error", "error": str(err)}
    if fails:
        return {"levels": levels, "pass": False, "first_fail": fails[0], "detail": levels[fails[0]]["detail"], "error": None}
    return {"levels": levels, "pass": True, "first_fail": None, "detail": "all applicable levels pass", "error": None}


# ------------------------------------------------------------------ aggregation
def _pct(num, den):
    return None if not den else 100.0 * num / den


def aggregate_method(rows):
    """rows: per-episode dicts with keys levels/pass/failure_mode/n_model_calls/wall_s. -> summary dict."""
    n = len(rows)
    per_level = {}
    for lv in LEVELS:
        app = [r for r in rows if r["levels"][lv]["status"] != "skip"]
        ok = [r for r in app if r["levels"][lv]["status"] == "pass"]
        accs = [r["levels"][lv].get("accuracy") for r in app if r["levels"][lv].get("accuracy") is not None]
        per_level[lv] = {"n_applicable": len(app), "n_pass": len(ok), "pct": _pct(len(ok), len(app)),
                         "mean_accuracy": (sum(accs) / len(accs)) if accs else None}
    n_pass = sum(1 for r in rows if r["pass"])
    n_sem = sum(1 for r in rows if all(r["levels"][lv]["status"] != "fail" for lv in SEMANTIC_LEVELS) and r["first_fail"] != "missing")
    calls = [r["n_model_calls"] for r in rows if r.get("n_model_calls") is not None]
    walls = [r["wall_s"] for r in rows if r.get("wall_s") is not None]
    by_mode = defaultdict(lambda: {"n": 0, "n_pass": 0})
    for r in rows:
        m = by_mode[r.get("failure_mode") or "?"]
        m["n"] += 1
        m["n_pass"] += int(r["pass"])
    for m in by_mode.values():
        m["pct"] = _pct(m["n_pass"], m["n"])
    return {"n_episodes": n, "n_predicted": sum(1 for r in rows if r["first_fail"] != "missing"),
            "n_pass": n_pass, "pct": _pct(n_pass, n), "levels": per_level, "n_semantic": n_sem, "pct_semantic": _pct(n_sem, n),
            "mean_calls": (sum(calls) / len(calls)) if calls else None,
            "mean_wall_s": (sum(walls) / len(walls)) if walls else None,
            "by_failure_mode": dict(by_mode)}


def score_methods(methods, episodes, ref_dir=REF_DIR, pred_dir=PRED_DIR):
    """-> {"methods": {m: {"summary", "episodes": [...]}}, "missing_references": [...]}"""
    refs, missing_refs = {}, []
    for ds, ep in episodes:
        r = load_json(Path(ref_dir) / ds / ep_name(ep))
        if r is None:
            missing_refs.append([ds, ep])
        else:
            refs[(ds, ep)] = r
    out = {"methods": {}, "missing_references": missing_refs, "n_episodes": len(episodes)}
    for m in methods:
        rows = []
        for ds, ep in episodes:
            ref = refs.get((ds, ep))
            if ref is None:
                continue
            pred = load_json(Path(pred_dir) / m / ds / ep_name(ep))
            res = score_episode(ref, pred)
            rows.append({"dataset": ds, "episode_index": ep, "failure_mode": ref.get("failure_mode"), "suite": ref.get("suite"),
                         "task_id": ref.get("task_id"), "pass": res["pass"], "first_fail": res["first_fail"], "detail": res["detail"],
                         "levels": res["levels"], "n_model_calls": (pred or {}).get("n_model_calls"),
                         "wall_s": (pred or {}).get("wall_s"), "peak_mem_gb": (pred or {}).get("peak_mem_gb"),
                         "error": (pred or {}).get("error")})
        out["methods"][m] = {"summary": aggregate_method(rows), "episodes": rows}
    return out


# ------------------------------------------------------------------ report
def _fmt_pct(v):
    return "-" if v is None else f"{v:.0f}%"


def _fmt_num(v, nd=1):
    return "-" if v is None else f"{v:.{nd}f}"


def render_markdown(result, which, methods):
    lines = [f"# Segmentation benchmark scoreboard ({which} set, {result['n_episodes']} episodes)", ""]
    if result["missing_references"]:
        lines.append(f"Missing references (excluded): {', '.join(f'{d}:{e}' for d, e in result['missing_references'])}")
        lines.append("")
    lines.append("## Per method")
    lines.append("")
    hdr = ["method", "episodes", "predicted"] + LEVELS + ["semantic", "overall", "mean calls", "mean wall_s"]
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    for m in methods:
        s = result["methods"][m]["summary"]
        cells = [m, str(s["n_episodes"]), str(s["n_predicted"])]
        for lv in LEVELS:
            L = s["levels"][lv]
            cells.append(f"{_fmt_pct(L['pct'])} ({L['n_pass']}/{L['n_applicable']})" if L["n_applicable"] else "n/a")
        cells += [f"{_fmt_pct(s.get('pct_semantic'))} ({s.get('n_semantic', 0)}/{s['n_episodes']})", f"{_fmt_pct(s['pct'])} ({s['n_pass']}/{s['n_episodes']})", _fmt_num(s["mean_calls"]), _fmt_num(s["mean_wall_s"])]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(f"Level percentages are over episodes where the level applies; held_state applies only when the method judged frames. "
                 f"overall = {', '.join(OVERALL_LEVELS)} all pass; {' and '.join(DIAGNOSTIC_LEVELS)} are diagnostic (shown, not part of overall). "
                 f"semantic = {', '.join(SEMANTIC_LEVELS)} all pass. events match at chunk granularity (|chunk(pred.last_before) - ref.chunk| <= {EVENT_CHUNK_TOL}); "
                 f"chunk_labels_1off = at most {ONE_OFF_MAX_WRONG} scorable chunk outside its allowed set.")
    lines.append("")

    modes = sorted({fm for m in methods for fm in result["methods"][m]["summary"]["by_failure_mode"]})
    lines.append("## Overall pass % by failure mode")
    lines.append("")
    hdr = ["method"] + modes
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    for m in methods:
        bm = result["methods"][m]["summary"]["by_failure_mode"]
        cells = [m] + [(f"{_fmt_pct(bm[fm]['pct'])} ({bm[fm]['n_pass']}/{bm[fm]['n']})" if fm in bm else "-") for fm in modes]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Per episode")
    lines.append("")
    hdr = ["method", "dataset", "ep", "failure_mode", "first failing level", "detail"]
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    for m in methods:
        for r in result["methods"][m]["episodes"]:
            ff = "PASS" if r["pass"] else r["first_fail"]
            detail = "" if r["pass"] else str(r["detail"]).replace("|", "/").replace("\n", " ")
            lines.append(f"| {m} | {r['dataset']} | {r['episode_index']} | {r['failure_mode']} | {ff} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--methods", nargs="+", required=True)
    ap.add_argument("--set", dest="which", choices=["dev", "heldout", "all"], default="dev")
    ap.add_argument("--name", default="scoreboard", help="output basename under outputs/bench/")
    ap.add_argument("--out-dir", default=str(WIN_OUT / "bench"))
    ap.add_argument("--episodes", nargs="*", default=None, help="explicit dataset:episode_index list (replaces --set)")
    args = ap.parse_args(argv)

    if args.episodes:
        episodes = [(s.rsplit(":", 1)[0], int(s.rsplit(":", 1)[1])) for s in args.episodes]
        args.which = "explicit"
    else:
        episodes = load_episode_set(args.which)
    result = score_methods(args.methods, episodes)
    result["set"] = args.which
    md = render_markdown(result, args.which, args.methods)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.name}.md").write_text(md, encoding="utf-8")
    dump_json(result, out_dir / f"{args.name}.json")
    print(md)
    print(f"wrote {out_dir / (args.name + '.md')} and .json")


if __name__ == "__main__":
    main()
