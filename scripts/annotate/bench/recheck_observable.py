"""Independent re-check of the frozen observable-only sparse annotations (outputs/observable_sparse_v1) against the
simulator's withheld state, computed directly from the recorded priv.* columns (not from Codex's facts.json).

For every labelled interval: does any frame contradict the label?
  failed_pickup       contradicted by a debounced two-finger hold of the target, or the target rising > 2 cm / moving > 5 cm
  controlled_transfer contradicted by any frame without a target hold, any frame resting (support or object contact),
                      a gripper contact with a non-target object, or an arm collision
For the UNLABELLED frames: which oracle events happened there (holds, drops/releases, failed attempts, wrong-object
contacts, collisions)? These are omissions, not contradictions, but the user should see them.
Usage: recheck_observable.py [--root outputs/observable_sparse_v1]"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import WIN_OUT, Episode, open_dataset  # noqa: E402


def runs(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(WIN_OUT / "observable_sparse_v1"))
    args = ap.parse_args()
    root = Path(args.root)
    manifest = {m["id"]: m for m in json.load(open(root / "private_manifest.json"))}
    facts = {f["id"]: f for f in json.load(open(root / "oracle_check" / "facts.json"))}
    intervals = defaultdict(list)  # id -> [(start, end_inclusive, label, event)]
    rows = list(csv.DictReader(open(root / "labelled_timesteps.csv", encoding="utf-8")))
    by_ep = defaultdict(list)
    for r in rows:
        by_ep[r["id"]].append((int(r["frame"]), r["label"], r["event"]))
    for eid, fr in by_ep.items():
        fr.sort()
        s = fr[0]
        prev = fr[0]
        for x in fr[1:] + [None]:
            if x is None or x[0] != prev[0] + 1 or x[1:] != prev[1:]:
                intervals[eid].append((s[0], prev[0], s[1], s[2]))
                if x is not None:
                    s = x
            if x is not None:
                prev = x

    report = {}
    total_contra = 0
    for eid in sorted(manifest):
        m = manifest[eid]
        ep = Episode(open_dataset(m["dataset"]), m["dataset"], m["episode_index"])
        slots = ep.meta["object_slots"]
        target = facts[eid]["target"]
        t = slots.index(target)
        n = ep.n
        gc = ep.col("priv.obj_gripper_contact") > 0
        lf, rf = ep.col("priv.obj_left_finger_contact") > 0, ep.col("priv.obj_right_finger_contact") > 0
        gr = ep.col("priv.obj_grasped") > 0
        sup, oo = ep.col("priv.obj_support_contact") > 0, ep.col("priv.obj_obj_contact") > 0
        pos = ep.col("priv.obj_pos").reshape(n, -1, 3)
        arm = ep.col("priv.arm_contacts").reshape(-1) > 0
        gfix = ep.col("priv.gripper_fixture_contacts").reshape(-1) > 0
        cmd, ap_ = ep.gripper_cmd, ep.gripper_aperture
        eef = ep.eef_xyz
        held = gr[:, t]
        # debounce: >= 3 consecutive grasp frames
        hold_runs = [(a, e) for a, e in runs(held) if e - a + 1 >= 3]
        held_deb = np.zeros(n, bool)
        for a, e in hold_runs:
            held_deb[a:e + 1] = True
        airborne = ~sup[:, t] & ~oo[:, t]
        wrong = [(slots[s], a, e) for s in range(len(slots)) if s != t and s < gc.shape[1] for a, e in runs(gc[:, s]) if e - a + 1 >= 3]
        coll = runs(arm)
        # failed attempts: CLOSE runs, no hold, aperture collapse >= 2 cm to <= 1.2 cm, contact or within 5 cm
        attempts = []
        for a, e in runs(cmd > 0):
            if e - a + 1 < 3 or held_deb[a:e + 1].any() or gfix[a:e + 1].any():
                continue
            seg = ap_[a:min(n, e + 3)]
            k = int(np.argmin(seg))
            if ap_[a] - seg[k] < 0.02 or seg[k] > 0.012:
                continue
            fmin = min(a + k, e)
            touch = (gc[a:fmin + 1, t] | lf[a:fmin + 1, t] | rf[a:fmin + 1, t]).any()
            near = np.linalg.norm(eef[fmin, :2] - pos[fmin, t, :2]) <= 0.05
            if touch or near:
                attempts.append((a, fmin, bool(touch)))
        drops = []
        for a, e in hold_runs:
            if e < n - 1:
                drops.append((e, "release" if cmd[min(n - 1, e + 1):min(n, e + 4)].min() <= 0 else "drop"))

        labelled = np.zeros(n, bool)
        seg_reports = []
        for (a, e, lab, ev) in intervals[eid]:
            labelled[a:e + 1] = True
            fr = slice(a, e + 1)
            contra = []
            if ev == "failed_pickup":
                if held_deb[fr].any():
                    contra.append(f"debounced target hold inside interval at frames {[i for i in range(a, e + 1) if held_deb[i]][:5]}")
                dz = float(pos[a:e + 1, t, 2].max() - pos[a, t, 2])
                dxy = float(np.linalg.norm(pos[e, t, :2] - pos[a, t, :2]))
                if dz > 0.02:
                    contra.append(f"target rose {dz*100:.1f} cm")
                if dxy > 0.05 and held[fr].any():
                    contra.append(f"target carried {dxy*100:.1f} cm while grasped")
            elif ev == "controlled_transfer":
                not_held = [i for i in range(a, e + 1) if not held[i]]
                rest = [i for i in range(a, e + 1) if not airborne[i]]
                if not_held:
                    contra.append(f"{len(not_held)} frames without target grasp (first {not_held[:5]})")
                if rest:
                    contra.append(f"{len(rest)} frames resting (first {rest[:5]})")
                w_in = [w for w in wrong if w[1] <= e and w[2] >= a]
                if w_in:
                    contra.append(f"wrong-object contact {w_in}")
                if arm[fr].any():
                    contra.append("arm collision frames inside")
            else:
                contra.append(f"unknown event type {ev}")
            total_contra += len(contra)
            seg_reports.append({"frames": [a, e], "label": lab, "event": ev, "n": e - a + 1,
                                "grasp_frames": int(held[fr].sum()), "airborne_frames": int(airborne[fr].sum()),
                                "contact_frames": int(gc[fr, t].sum()), "contradictions": contra})
        # omissions: oracle events fully outside labelled frames
        def outside(a, e):
            return not labelled[a:e + 1].any()
        om = {
            "holds_outside": [(a, e) for a, e in hold_runs if outside(a, e)],
            "holds_partially_outside": [(a, e, int((~labelled[a:e + 1]).sum())) for a, e in hold_runs if not outside(a, e) and (~labelled[a:e + 1]).any()],
            "drops_or_releases": [(f, k, bool(labelled[f])) for f, k in drops],
            "attempts": [(a, e, touch, bool(labelled[a:e + 1].any())) for a, e, touch in attempts],
            "wrong_object_contacts": wrong,
            "collisions": [(a, e) for a, e in coll if e - a + 1 >= 3],
        }
        report[eid] = {"dataset": m["dataset"], "episode": m["episode_index"], "target": target, "success": bool(ep.success),
                       "n_frames": n, "labelled_frames": int(labelled.sum()), "segments": seg_reports, "oracle_events": om}
        print(f"\n== {eid} {m['dataset']} ep{m['episode_index']} target={target} success={ep.success} frames={n} labelled={int(labelled.sum())}")
        for sr in seg_reports:
            flag = "CONTRADICTION" if sr["contradictions"] else "ok"
            print(f"   {sr['frames'][0]:>3}-{sr['frames'][1]:<3} {sr['event']:19s} grasp {sr['grasp_frames']:>3}/{sr['n']:<3} airborne {sr['airborne_frames']:>3} contact {sr['contact_frames']:>3}  {flag} {sr['contradictions'] or ''}")
        print(f"   oracle holds (>=3 frames): {hold_runs}")
        print(f"   hold ends: {drops}")
        print(f"   failed attempts (a, min-aperture frame, contact, labelled?): {om['attempts']}")
        print(f"   holds fully outside labels: {om['holds_outside']}; partially outside: {om['holds_partially_outside']}")
        print(f"   wrong-object contacts: {wrong}; collisions: {om['collisions']}")
    out = root / "oracle_check" / "recheck.json"
    json.dump(report, open(out, "w"), indent=1, default=str)
    print(f"\ncontradictions total: {total_contra}; wrote {out}")


if __name__ == "__main__":
    main()
