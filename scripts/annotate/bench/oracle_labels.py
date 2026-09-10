"""Export training labels from the oracle references (docs/segmentation_benchmark.md section 1, reference r6).

The VLM annotators were benchmarked and are not reliable enough (docs/segmentation_benchmark.md, Status), so the
learner's labels come from the simulator oracle. One row per FRAME (same layout as to_labels.py for VLM records):

  dataset, episode_index, frame_index, global_index (dataset_from_index + frame_index), chunk,
  label            = the chunk's primary label (progress | failure_inducing | recovery | neutral | aftermath)
  allowed          = the chunk's allowed set, "|"-joined
  q                = rule ambiguity weight (not calibrated confidence): 1.0 one allowed label, 0.5 two, 0.25 three or more, 0.0 rule "unlocalised*"
  cause, failure_mode, decisive_error_chunk (= reference decisive_chunk, t*),
  failure_onset_chunk    = first chunk whose allowed set is exactly {failure_inducing} (first error), else decisive
  visible_failure_chunk  = decisive (for now)
  recoverable_until_chunk= null (to be filled by the recovery-branching oracle)
  event_type_in_chunk    = grasp | drop | release | none (first event of the chunk)
  event_at_frame         = grasp | drop | release | none, on the event's OWN frame (see event_frames)
  event_target           = that event acts on the episode's target object
  event_hold_frames      = length of the hold the event starts (grasp) or ends (drop/release), -1 if none
  event_missed_release   = the release did not leave the target at the goal
  held             = the target is held in this frame (held_runs state "held")
  success, source = "oracle_r6"

Also writes a per-episode table (dataset, episode_index, success, failure_mode, cause, decisive_chunk, n_chunks,
n_events, frac_q1 = fraction of chunks with q == 1).

Usage: oracle_labels.py --datasets prefix ... [--out $FTL_PROJ/bench/oracle_labels.parquet]
                        [--episodes-out $FTL_PROJ/bench/oracle_episodes.parquet]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/annotate: common.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, list_datasets  # noqa: E402
from oracle_reference import BENCH, LABELS, REF_DIR, REFERENCE_VERSION  # noqa: E402

SOURCE = f"oracle_{REFERENCE_VERSION}"
EVENT_TYPES = ("grasp", "drop", "release")
LANDMARKS = ("decisive_error_chunk", "failure_onset_chunk", "visible_failure_chunk", "recoverable_until_chunk")


def q_of(allowed, rule):
    """Oracle confidence of a chunk label from the size of its allowed set; 0 when the reference is unlocalised."""
    if str(rule).split("+")[0].startswith("unlocalised"):
        return 0.0
    k = len(set(allowed))
    return 1.0 if k <= 1 else (0.5 if k == 2 else 0.25)


def event_type_by_chunk(ref):
    """{chunk: type} of the first (earliest) grasp/drop/release event in each chunk."""
    out = {}
    for ev in sorted(ref.get("events", []), key=lambda e: (e["index"], e["type"] != "grasp")):
        if ev["type"] in EVENT_TYPES:
            out.setdefault(int(ev["chunk"]), ev["type"])
    return out


def event_frames(ref):
    """Per-frame event localisation: what happens AT this frame, not merely somewhere in its chunk.

    `event_type_in_chunk` names the chunk's first event but not when inside the chunk it happened, so a
    reward built from it lands on an arbitrary frame of the chunk - and disagrees with `held`, which is
    per frame. These four columns put each event on its own frame:

      event_at_frame        grasp | drop | release | none, at exactly the event's frame index
      event_target          the object of that event is the episode's target object
      event_hold_frames     length of the hold this event starts (grasp) or ends (drop/release), -1 if none
      event_missed_release  a release of the target that did not leave it at the goal

    A release is "missed" unless it is the last target event of a SUCCESSFUL episode: that one is the
    placement the task asked for, and every other release put the target down somewhere it did not
    belong (in a failed episode no release achieved the goal, by definition of the episode outcome).
    """
    n = int(ref["n_frames"])
    kind = np.full(n, "none", object)
    is_target = np.zeros(n, bool)
    hold = np.full(n, -1, int)
    missed = np.zeros(n, bool)
    target = ref.get("target_slot")
    evs = [e for e in ref.get("events", []) if e["type"] in EVENT_TYPES and 0 <= int(e["index"]) < n]
    tgt = [e for e in evs if target is not None and e["object"] == target]
    placed = tgt[-1] if (bool(ref["success"]) and tgt and tgt[-1]["type"] == "release") else None
    for e in evs:
        i = int(e["index"])
        if kind[i] != "none":  # two events on one frame (they sort grasp-first): keep the first
            continue
        on_target = target is not None and e["object"] == target
        kind[i] = e["type"]
        is_target[i] = on_target
        hold[i] = int(e.get("hold_frames", -1))
        missed[i] = e["type"] == "release" and on_target and e is not placed
    return kind, is_target, hold, missed


def held_by_frame(ref):
    """bool per frame: inside a held run (state 'held'); ambiguous and empty frames are False."""
    n = int(ref["n_frames"])
    held = np.zeros(n, bool)
    for r in ref.get("held_runs", []):
        if r["state"] == "held":
            held[int(r["start"]):int(r["end"]) + 1] = True
    return held


def failure_onset_chunk(ref):
    """First chunk whose allowed set is exactly {failure_inducing}; else the decisive chunk (may be None)."""
    for cl in ref["chunk_labels"]:
        if set(cl["allowed"]) == {"failure_inducing"}:
            return int(cl["chunk"])
    return ref.get("decisive_chunk")


def frame_table(ref, g0):
    """Per-frame DataFrame of one reference; g0 = dataset_from_index of the episode."""
    chunks = ref["chunks"]
    cls = ref["chunk_labels"]
    if len(cls) != len(chunks):
        raise ValueError(f"{ref['dataset']} ep{ref['episode_index']}: {len(cls)} chunk labels for {len(chunks)} chunks")
    n = int(ref["n_frames"])
    sizes = np.array([b - a for a, b in chunks], int)
    if sizes.sum() != n or (sizes <= 0).any():
        raise ValueError(f"{ref['dataset']} ep{ref['episode_index']}: chunks do not tile {n} frames")
    ev_type = event_type_by_chunk(ref)
    ev_kind, ev_target, ev_hold, ev_missed = event_frames(ref)
    rep = lambda vals: np.repeat(np.asarray(vals, object), sizes)  # noqa: E731
    dec = ref.get("decisive_chunk")
    onset = failure_onset_chunk(ref)
    df = pd.DataFrame({
        "dataset": ref["dataset"], "episode_index": int(ref["episode_index"]),
        "frame_index": np.arange(n), "global_index": int(g0) + np.arange(n),
        "chunk": np.repeat(np.arange(len(chunks)), sizes),
        "label": rep([cl["primary"] for cl in cls]),
        "allowed": rep(["|".join(cl["allowed"]) for cl in cls]),
        "q": np.repeat(np.array([q_of(cl["allowed"], cl["rule"]) for cl in cls], float), sizes),
        "rule": rep([cl["rule"] for cl in cls]),
        "cause": ref.get("cause"), "failure_mode": ref["failure_mode"],
        "decisive_error_chunk": dec, "failure_onset_chunk": onset, "visible_failure_chunk": dec, "recoverable_until_chunk": None,
        "event_type_in_chunk": rep([ev_type.get(c, "none") for c in range(len(chunks))]),
        "event_at_frame": ev_kind, "event_target": ev_target,
        "event_hold_frames": ev_hold, "event_missed_release": ev_missed,
        "held": held_by_frame(ref),
        "success": bool(ref["success"]), "source": SOURCE,
    })
    for k in LANDMARKS:
        df[k] = df[k].astype("Int64")
    return df


def episode_row(ref):
    qs = [q_of(cl["allowed"], cl["rule"]) for cl in ref["chunk_labels"]]
    return {
        "dataset": ref["dataset"], "episode_index": int(ref["episode_index"]), "success": bool(ref["success"]),
        "failure_mode": ref["failure_mode"], "cause": ref.get("cause"), "decisive_chunk": ref.get("decisive_chunk"),
        "n_chunks": len(ref["chunk_labels"]), "n_events": len(ref.get("events", [])),
        "frac_q1": float(np.mean([q == 1.0 for q in qs])) if qs else 0.0,
        "n_failure_inducing": sum(cl["primary"] == "failure_inducing" for cl in ref["chunk_labels"]),
    }


def dataset_from_index(name):
    """{episode_index: dataset_from_index} from the LeRobot meta/episodes parquet files (as to_labels.py)."""
    out = {}
    meta_dir = DATA / name / "meta" / "episodes"
    for p in sorted(meta_dir.rglob("*.parquet")):
        t = pd.read_parquet(p, columns=["episode_index", "dataset_from_index"])
        out.update(dict(zip(t["episode_index"].astype(int), t["dataset_from_index"].astype(int))))
    if not out:
        raise FileNotFoundError(f"no meta/episodes parquet under {meta_dir}")
    return out


def load_references(names, ref_dir=REF_DIR):
    for name in names:
        d = ref_dir / name
        if not d.exists():
            continue
        for p in sorted(d.glob("episode_*.json")):
            yield name, json.loads(p.read_text())


def report(df, eps):
    """Print the distributions the learner cares about."""
    print(f"\n== {len(eps)} episodes ({int(eps['success'].sum())} successes), {len(df)} frames")
    for flag, title in ((True, "successes"), (False, "failures")):
        sub = df[df["success"] == flag]
        if len(sub):
            vc = sub["label"].value_counts()
            print(f"  label distribution over frames, {title} ({len(sub)}): " + ", ".join(f"{k}={v} ({v / len(sub):.1%})" for k, v in vc.items()))
    qc = df["q"].value_counts().sort_index()
    print("  q histogram (frames): " + ", ".join(f"q={q:g}: {c} ({c / len(df):.1%})" for q, c in qc.items()))
    for flag, title in ((True, "successes"), (False, "failures")):
        sub = df[df["success"] == flag]
        if len(sub):
            qc = sub["q"].value_counts().sort_index()
            print(f"    {title}: " + ", ".join(f"q={q:g}: {c / len(sub):.1%}" for q, c in qc.items()))
    fails = eps[~eps["success"]]
    if len(fails):
        nul = int(fails["decisive_chunk"].isna().sum())
        print(f"  decisive-null rate among failures: {nul}/{len(fails)} ({nul / len(fails):.1%})")
        print("  mean failure_inducing chunks per episode, by failure_mode:")
        for mode, g in fails.groupby("failure_mode"):
            print(f"    {mode:18s} n={len(g):4d}  mean={g['n_failure_inducing'].mean():.2f}  frac_q1={g['frac_q1'].mean():.2f}")
    succ = eps[eps["success"]]
    if len(succ):
        rec = int(succ["decisive_chunk"].notna().sum())
        print(f"  successes with a recovered error (decisive set): {rec}/{len(succ)}; cause: {succ['cause'].value_counts().to_dict()}")
        rc = Counter(r.split("+")[0] for r in df.loc[df["success"], "rule"].drop_duplicates().tolist())
        print(f"  rules present in success chunks: {sorted(rc)}")
    ev = df.drop_duplicates(["dataset", "episode_index", "chunk"])["event_type_in_chunk"].value_counts()
    print("  event_type_in_chunk (chunks): " + ", ".join(f"{k}={v}" for k, v in ev.items()))
    at = df.loc[df["event_at_frame"] != "none"]
    print("  event_at_frame (frames): " + ", ".join(f"{k}={v}" for k, v in at["event_at_frame"].value_counts().items())
          + f"; on the target {int(at['event_target'].sum())}"
          + f"; missed releases {int(df['event_missed_release'].sum())}"
          + f"; target grasps holding >= 8 frames "
            f"{int(((df['event_at_frame'] == 'grasp') & df['event_target'] & (df['event_hold_frames'] >= 8)).sum())}")
    print(f"  held frames: {df['held'].mean():.1%}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datasets", nargs="+", required=True, help="dataset names or family prefixes")
    ap.add_argument("--out", default=str(BENCH / "oracle_labels.parquet"))
    ap.add_argument("--episodes-out", default=str(BENCH / "oracle_episodes.parquet"))
    args = ap.parse_args()
    names = list_datasets(args.datasets)
    frames, episodes, missing = [], [], Counter()
    g0_cache = {}
    for name, ref in load_references(names):
        if ref.get("reference_version") != REFERENCE_VERSION:
            missing[f"version {ref.get('reference_version')}"] += 1
            continue
        if name not in g0_cache:
            g0_cache[name] = dataset_from_index(name)
        g0 = g0_cache[name].get(int(ref["episode_index"]))
        if g0 is None:
            missing["no dataset_from_index"] += 1
            continue
        frames.append(frame_table(ref, g0))
        episodes.append(episode_row(ref))
    if not frames:
        sys.exit(f"no {REFERENCE_VERSION} references under {REF_DIR} for {names}")
    df = pd.concat(frames, ignore_index=True)
    eps = pd.DataFrame(episodes)
    assert set(df["label"].unique()) <= set(LABELS), df["label"].unique()
    out, eout = Path(args.out), Path(args.episodes_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    eps.to_parquet(eout, index=False)
    print(f"{len(eps)} episodes, {len(df)} frames -> {out}\n{len(eps)} rows -> {eout}")
    if missing:
        print(f"skipped: {dict(missing)}")
    report(df, eps)


if __name__ == "__main__":
    main()
