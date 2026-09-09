"""Held-state and grasp/drop/release events from NON-privileged gripper telemetry, and their accuracy against the
oracle references.

Hypothesis: with the command CLOSE (action[6] > 0) the fingers settle at the object's width when something is held
(roughly 0.6-3.6 cm on the observation.state[6] finger coordinate) and near 0 when nothing is grasped; command OPEN
means empty. The visual VLM detector misses flat boxes; telemetry may be far more accurate and is available on real
robots too (gripper width is proprioception, not privileged state).

Per-frame rule (cfg):
  held      = cmd > 0 and lo <= ap <= hi and the aperture is settled (|d ap| < settle_tol for settle_frames frames)
  empty     = cmd <= 0, or ap > hi, or (cmd > 0 and ap < lo)
  uncertain = cmd > 0 and lo <= ap <= hi but not settled (fingers still closing/opening)
then held runs shorter than min_run frames are dropped; events are the transitions of the held runs.

Usage: telemetry_held.py --datasets full_shift8 ... [--sweep] [--limit N]
"""
import argparse
import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJ, Episode, list_datasets, open_dataset  # noqa: E402

BENCH = Path(PROJ) / "bench"
TOL = 3  # event bracket tolerance in frames (score.py)


@dataclass
class TelemetryCfg:
    held_lo_m: float = 0.005
    held_hi_m: float = 0.036
    min_run: int = 3
    settle_frames: int = 3
    settle_tol_m: float = 0.0005  # per-frame aperture change below which the fingers count as settled
    flip_ignore: int = 0  # frames after a command sign change that are forced to uncertain (fingers travelling)


def held_state_from_telemetry(ap, cmd, cfg=TelemetryCfg()):
    ap = np.asarray(ap, float)
    cmd = np.asarray(cmd, float)
    n = len(ap)
    dap = np.abs(np.diff(ap, prepend=ap[0]))
    settled = np.ones(n, bool)
    for k in range(cfg.settle_frames):
        shifted = np.roll(dap, k)
        shifted[:k] = dap[0]
        settled &= shifted < cfg.settle_tol_m
    in_win = (cmd > 0) & (ap >= cfg.held_lo_m) & (ap <= cfg.held_hi_m)
    state = np.full(n, "empty", dtype=object)
    state[in_win & settled] = "held"
    state[in_win & ~settled] = "uncertain"
    if cfg.flip_ignore > 0:
        flips = np.flatnonzero(np.sign(cmd[1:]) != np.sign(cmd[:-1])) + 1
        for f in flips:
            state[f : min(n, f + cfg.flip_ignore)] = "uncertain"
    # drop held runs shorter than min_run (turn them into uncertain)
    i = 0
    while i < n:
        if state[i] == "held":
            j = i
            while j + 1 < n and state[j + 1] == "held":
                j += 1
            if j - i + 1 < cfg.min_run:
                state[i : j + 1] = "uncertain"
            i = j + 1
        else:
            i += 1
    # uncertain frames between two held frames (settling wobble inside a hold) become held
    i = 0
    while i < n:
        if state[i] == "uncertain":
            j = i
            while j + 1 < n and state[j + 1] == "uncertain":
                j += 1
            if i > 0 and j + 1 < n and state[i - 1] == "held" and state[j + 1] == "held":
                state[i : j + 1] = "held"
            i = j + 1
        else:
            i += 1
    return state


def held_runs(state):
    runs, i, n = [], 0, len(state)
    while i < n:
        if state[i] == "held":
            j = i
            while j + 1 < n and state[j + 1] == "held":
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1
    return runs


def events_from_states(state, cmd):
    cmd = np.asarray(cmd, float)
    n = len(state)
    evs = []
    for a, e in held_runs(state):
        if a > 0:
            evs.append({"type": "grasp", "last_before": a - 1, "first_after": a})
        if e < n - 1:
            window = cmd[e + 1 : min(n, e + 4)]
            typ = "release" if (len(window) and window.min() <= 0) else "drop"
            evs.append({"type": typ, "last_before": e, "first_after": e + 1})
    return evs


def expand_reference(ref, min_hold=0, gap=0):
    """Per-frame reference state. With min_hold/gap, held runs separated by <= gap frames are merged and held runs
    shorter than min_hold frames become ambiguous (an event shorter than that is below annotation granularity)."""
    n = ref["n_frames"]
    st = np.full(n, "empty", dtype=object)
    for r in ref["held_runs"]:
        st[r["start"] : r["end"] + 1] = r["state"]
    if min_hold or gap:
        runs = held_runs(st)
        merged = []
        for a, e in runs:
            if merged and a - merged[-1][1] - 1 <= gap:
                st[merged[-1][1] + 1 : a] = "held"
                merged[-1] = (merged[-1][0], e)
            else:
                merged.append((a, e))
        for a, e in merged:
            if e - a + 1 < min_hold:
                st[a : e + 1] = "ambiguous"
    return st


def reference_events(ref, st, cmd):
    """Events implied by a (possibly re-debounced) reference state array. Ambiguous frames (one-finger contact,
    transition frames) inherit the preceding decided state so that the 2 ambiguous frames at the end of a hold that
    reaches the episode end do not fabricate a release event."""
    filled = np.array(st, dtype=object)
    prev = "empty"
    for i in range(len(filled)):
        if filled[i] == "ambiguous":
            filled[i] = prev
        else:
            prev = filled[i]
    return events_from_states(filled, cmd)


def events_pass(pred, ref_events, tol=TOL):
    used = set()
    for r in ref_events:
        lo, hi = r["last_before"] - tol, r["first_after"] + tol
        hit = None
        for k, p in enumerate(pred):
            if k in used or p["type"] != r["type"]:
                continue
            if p["last_before"] <= hi and p["first_after"] >= lo:
                hit = k
                break
        if hit is None:
            return False, f"ref {r['type']} [{r['last_before']},{r['first_after']}] unmatched"
        used.add(hit)
    if len(used) != len(pred):
        extra = [p for k, p in enumerate(pred) if k not in used][0]
        return False, f"extra {extra['type']} [{extra['last_before']},{extra['first_after']}]"
    return True, ""


def load_refs(names, limit=None):
    out = []
    for name in names:
        d = BENCH / "references" / name
        if not d.exists():
            continue
        for p in sorted(d.glob("episode_*.json")):
            out.append(json.loads(p.read_text()))
            if limit and len(out) >= limit:
                return out
    return out


def evaluate(refs, tele, cfg, verbose=False, ref_min_hold=0, ref_gap=0, tol=TOL, chunk_tol=None):
    per_ep, by_obj_held, by_obj_closed_empty = [], defaultdict(list), defaultdict(list)
    for ref in refs:
        ap, cmd = tele[(ref["dataset"], ref["episode_index"])]
        st = held_state_from_telemetry(ap, cmd, cfg)
        rs = expand_reference(ref, ref_min_hold, ref_gap)
        ref_evs = reference_events(ref, rs, cmd) if (ref_min_hold or ref_gap) else ref["events"]
        t = tol if chunk_tol is None else chunk_tol * 10
        scorable = rs != "ambiguous"
        correct = (st == rs) & scorable
        acc = correct.sum() / max(scorable.sum(), 1)
        evs = events_from_states(st, cmd)
        ok, why = events_pass(evs, ref_evs, t)
        wrong = np.flatnonzero(scorable & (st != rs))
        reason = ""
        if len(wrong):
            f = int(wrong[0])
            reason = f"frame {f}: telemetry {st[f]} (ap {ap[f]*100:.2f} cm, cmd {cmd[f]:+.0f}) vs ref {rs[f]} ({len(wrong)} wrong)"
        per_ep.append({"dataset": ref["dataset"], "ep": ref["episode_index"], "mode": ref["failure_mode"], "target": ref.get("target_slot"),
                       "acc": float(acc), "events_ok": ok, "events_why": why, "reason": reason, "n_events_ref": len(ref_evs), "n_events_pred": len(evs)})
        tgt = ref.get("target_slot") or "none"
        held_mask = rs == "held"
        by_obj_held[tgt].extend((ap[held_mask] * 100).tolist())
        ce = (rs == "empty") & (cmd > 0)
        by_obj_closed_empty[tgt].extend((ap[ce] * 100).tolist())
    accs = np.array([r["acc"] for r in per_ep])
    ev_ok = np.array([r["events_ok"] for r in per_ep])
    summary = {"cfg": asdict(cfg), "episodes": len(per_ep), "frame_acc_mean": float(accs.mean()), "episodes_100pct_frames": float((accs >= 0.9999).mean()),
               "episodes_ge_99pct_frames": float((accs >= 0.99).mean()), "episodes_events_pass": float(ev_ok.mean()),
               "both_pass": float(((accs >= 0.9999) & ev_ok).mean())}
    return summary, per_ep, by_obj_held, by_obj_closed_empty


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", required=True)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ref-min-hold", type=int, default=0, help="reference held runs shorter than this become ambiguous")
    ap.add_argument("--ref-gap", type=int, default=0, help="merge reference held runs separated by <= this many frames")
    ap.add_argument("--chunk-tol", type=int, default=None, help="match events at chunk granularity: +- this many chunks (10 frames each)")
    args = ap.parse_args()
    names = list_datasets(args.datasets)
    refs = load_refs(names, args.limit)
    print(f"{len(refs)} references", flush=True)
    tele, cache = {}, {}
    npz = BENCH / "telemetry_cache.npz"
    if npz.exists():
        z = np.load(npz, allow_pickle=True)
        tele = {tuple(k.split("|")) if False else (k.rsplit("|", 1)[0], int(k.rsplit("|", 1)[1])): (z[k][0], z[k][1]) for k in z.files}
        print(f"telemetry cache: {len(tele)} episodes", flush=True)
    for i, ref in enumerate(refs):
        if (ref["dataset"], ref["episode_index"]) in tele:
            continue
        name = ref["dataset"]
        if name not in cache:
            cache = {name: open_dataset(name)}  # one dataset open at a time
        ep = Episode(cache[name], name, ref["episode_index"])
        tele[(name, ref["episode_index"])] = (ep.gripper_aperture.copy(), ep.gripper_cmd.copy())
        if (i + 1) % 50 == 0:
            print(f"  loaded {i + 1}/{len(refs)}", flush=True)
    np.savez(npz, **{f"{k[0]}|{k[1]}": np.stack([v[0], v[1]]) for k, v in tele.items()})

    cfg = TelemetryCfg()
    if args.sweep:
        results = []
        for lo in (0.002, 0.004, 0.006):
            for hi in (0.034, 0.038, 0.041):
                for mr in (3, 6, 8):
                    for sf in (0, 2):
                      for fi in (0, 4, 8):
                        c = replace(cfg, held_lo_m=lo, held_hi_m=hi, min_run=mr, settle_frames=sf, flip_ignore=fi)
                        s, _, _, _ = evaluate(refs, tele, c, ref_min_hold=args.ref_min_hold, ref_gap=args.ref_gap, chunk_tol=args.chunk_tol)
                        results.append(s)
        results.sort(key=lambda s: (s["both_pass"], s["episodes_events_pass"], s["frame_acc_mean"]), reverse=True)
        print("\n== sweep top 8 (by episodes passing both frame-100% and events)")
        for s in results[:8]:
            print(f"  {s['cfg']}  both={s['both_pass']:.3f} events={s['episodes_events_pass']:.3f} frames100={s['episodes_100pct_frames']:.3f} "
                  f"frames99={s['episodes_ge_99pct_frames']:.3f} acc={s['frame_acc_mean']:.4f}")
        cfg = TelemetryCfg(**results[0]["cfg"])

    summary, per_ep, held_d, ce_d = evaluate(refs, tele, cfg, ref_min_hold=args.ref_min_hold, ref_gap=args.ref_gap, chunk_tol=args.chunk_tol)
    summary["ref_min_hold"], summary["ref_gap"], summary["chunk_tol"] = args.ref_min_hold, args.ref_gap, args.chunk_tol
    print("\n== summary", json.dumps(summary, indent=1))
    modes = defaultdict(list)
    for r in per_ep:
        modes[r["mode"]].append(r)
    print("\n== by failure mode: n, mean frame acc, frames-100%, events pass")
    for m, rs in sorted(modes.items()):
        print(f"  {m:18s} n={len(rs):3d} acc={np.mean([r['acc'] for r in rs]):.4f} f100={np.mean([r['acc'] >= 0.9999 for r in rs]):.2f} ev={np.mean([r['events_ok'] for r in rs]):.2f}")
    print("\n== aperture (cm) while reference HELD, per target: median [p5, p95] n   |   while CLOSE and reference EMPTY: median [p5,p95] n")
    for obj in sorted(set(list(held_d) + list(ce_d))):
        h, c = np.array(held_d.get(obj, [])), np.array(ce_d.get(obj, []))
        hs = f"{np.median(h):.2f} [{np.percentile(h, 5):.2f},{np.percentile(h, 95):.2f}] n={len(h)}" if len(h) else "-"
        cs = f"{np.median(c):.2f} [{np.percentile(c, 5):.2f},{np.percentile(c, 95):.2f}] n={len(c)}" if len(c) else "-"
        print(f"  {obj:24s} held {hs:36s} | closed-empty {cs}")
    print("\n== worst 20 episodes by frame accuracy")
    for r in sorted(per_ep, key=lambda r: r["acc"])[:20]:
        print(f"  {r['dataset']:20s} ep{r['ep']:3d} {r['mode']:16s} acc={r['acc']:.3f} events_ok={r['events_ok']} {r['reason']} | {r['events_why']}")
    print("\n== episodes failing events but with >= 99% frames (first 20)")
    for r in [r for r in per_ep if not r["events_ok"] and r["acc"] >= 0.99][:20]:
        print(f"  {r['dataset']:20s} ep{r['ep']:3d} {r['mode']:16s} ref_ev={r['n_events_ref']} pred_ev={r['n_events_pred']} {r['events_why']}")
    out = BENCH / "telemetry_held_eval.json"
    out.write_text(json.dumps({"summary": summary, "per_episode": per_ep}, indent=1))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
