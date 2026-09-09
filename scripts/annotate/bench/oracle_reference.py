"""Oracle reference builder for the segmentation benchmark (docs/segmentation_benchmark.md, section 1, version r6).

Builds, from priv.* columns only, the per-episode ground truth: run-length held state, grasp/drop/release
events, wrong-object contacts, collisions, fixture motion, stage frames, failure_mode + cause, decisive chunk and
per-chunk allowed label sets. Deterministic, pure numpy.

r6: failed acquisition credit follows complete holds across chunk boundaries.
Mixed errors and partial failed attempts admit only failure_inducing/neutral;
empty retry approaches and movement before a later grasp receive neutral credit.

Reading of the contract that needed a decision (each is visible in the output through "rule"/"mode_reason"):
  * held state is debounced with hysteresis per slot: a switch to held needs >= DEBOUNCE consecutive grasped
    frames, a switch back to empty needs >= DEBOUNCE consecutive non-grasped frames (1-2 frame flag gaps inside a
    hold stay held; 1-2 frame grasped blips outside a hold stay non-held).
  * r2, annotation granularity: debounced holds separated by <= HOLD_GAP_FRAMES frames are merged into one hold, and
    only holds of >= HOLD_MIN_FRAMES frames count as holds ("held" state, grasp/drop/release events, failure-mode
    logic) unless they are slips (r3, next bullet). Shorter debounced holds that are not slips (pushing a bowl with
    the fingertips, a brush with both pads) stay in held_runs as "ambiguous" frames and produce no event.
  * r3, slips: a debounced hold of ANY length is a real hold when the object was airborne (no support and no
    object-object contact) at some frame of it, or when it ends with the command still CLOSE and the aperture
    collapses below CLOSED_APERTURE within SLIP_COLLAPSE_FRAMES frames after it (the fingers closed on nothing after
    losing the object). r2 demoted every hold shorter than 8 frames, which erased 7-frame lifts (full_shift8__t1
    ep 3, frames 150-156) and let the following close-on-nothing carry the error into the next chunk.
  * r3, post-slip closures: a close-on-nothing run that begins within POST_SLIP_FRAMES frames after a drop (any hold
    that ended with the command CLOSE) is the same failed attempt (the empty gripper finishing its closing motion);
    it is listed under "post_slip_closure" and is NOT an error of its own (no failure_inducing chunk, not a failed
    closure for the missed_grasp decisive chunk), so the error sits in the drop's chunk.
  * ambiguous frames: the 2 frames on EACH side of every hold boundary (a-2..a+1 and b-1..b+2), frames where
    exactly one finger touches an object (left XOR right), grasped-flag blips and short holds that did not pass
    debouncing / HOLD_MIN_FRAMES (and are not slips), and flag gaps inside a hold (including merged gaps).
  * event chunk = chunk of `last_before` (the observation at first_after results from the action of the
    previous frame); if last_before and first_after fall in different chunks the second chunk also admits
    failure_inducing ("+decisive_boundary").
  * a hold whose last frame is within DEBOUNCE frames of the episode end is "held at end": the state after the
    transition never stabilises for DEBOUNCE frames, so no drop/release event is emitted for it and the episode takes
    the held-at-end branch (hold_no_release / stall_after_grasp).
  * target / goal come from the sidecar goal_state ('on'/'in' atoms), not from target_mask order: the mask is
    slot-ordered and puts the goal first for e.g. libero_goal task 6 (bowl slot 0, cream cheese slot 1). Fallback
    to the mask (episode_progress.py convention) when goal_state has no movable object.
  * tasks with several movable targets or extra fixture atoms (turnon/open/close) cannot be resolved when the
    last hold ends in a release (was it a correct sub-placement?): failure_mode "other" rather than a guess.
  * a >= 5 frame run where the target is airborne and in gripper contact but the grasped flag is off means the
    flag missed a real hold; events would be wrong, so the episode is "other" (mode_reason says why).
  * close-on-nothing = cmd CLOSE, aperture (observation.state[6]) < 0.8 cm, no debounced hold, no gripper
    contact with any object, >= 2 frames.
  * held at the end is ALWAYS the held-at-end branch (r2; r1 treated a hold that was still moving at timeout as a
    late attempt and blamed the last prior drop/release/close-on-nothing, which labelled the final carry
    "aftermath"). hold_no_release vs stall_after_grasp: both need a final idle run (>= 10 frames) for a decisive
    chunk (the chunk where motion stops); stall_after_grasp needs >= 40 idle frames AND the target far from the goal
    (never transported, > 12 cm). A hold that is still moving at timeout (no final idle run) is hold_no_release with
    decisive_chunk null (the contract's "chunk where motion stops" does not exist), whatever happened before.
  * r3, decisive null with known events: an episode whose decisive chunk does not exist (hold still moving at timeout;
    "other" with an unresolved multi-target / fixture-atom release) but whose events are known gets chunk labels from
    the events with the pre-decisive rules (drops / slips / close-on-nothing / wrong grasps -> {failure_inducing},
    re-grasps after an error -> {recovery}, stage advances -> {progress}, idle -> {neutral}, otherwise
    {progress, neutral}); chunks during the final hold that are neither an advance nor idle are "final_hold_active"
    ({progress, neutral}, primary progress). r2 labelled every chunk of such an episode "unlocalised_<mode>" with all
    five labels (unscorable, q = 0 in the training export). The unscorable rule remains for never_reached episodes
    and for episodes without usable events (missed_grasp without a hold or a closure, "other" because the grasped
    flag missed an airborne hold, fixture-only tasks).
  * a debounced hold that never lifted the object (support contact on every frame) and then ended, by drop or by
    release, is a failed grasp attempt: the episode is missed_grasp when it is the last hold, and the event
    counts as a failed closure (like close-on-nothing) for the missed_grasp decisive chunk (first failed closure
    after first target contact).
  * chunk labels after the decisive chunk while the target is held (any frame of the chunk inside a hold, and the
    chunk holds no grasp/drop/close-on-nothing/wrong-grasp event): the oracle cannot judge a late carry, allowed
    {progress, recovery, neutral, aftermath} (rule "post_held_unscorable"; still scorable: failure_inducing fails).
  * successful episodes (mode "success", training labels only; the benchmark scores failures) use the pre-decisive
    rules with the outcome known: a stage advance (incl. "placed" = the chunk whose action first satisfies the
    success predicate) or a carry towards the goal -> {progress}; idle -> {neutral}; otherwise {progress, neutral}.
    A drop / close-on-nothing / wrong grasp followed by a later grasp of a task object is a recovered error
    ({failure_inducing}, rule "other_event") and that later grasp is {recovery} ("regrasp"); the first recovered
    error sets decisive_chunk and the cause (drop, close_on_nothing -> grasp; wrong_grasp -> sequencing_semantic),
    otherwise decisive_chunk is null and the cause "unclear". The release that lets go of an object for good is the
    placement ({progress}, "place_release"); a drop that is never followed by a re-grasp cannot be told from a
    placement ({progress, neutral}, "drop_final"). Chunks starting after the success frame -> {neutral, aftermath}
    ("post_success"). Success-only readings: a close-on-nothing is a miss only when it touches no fixture (pressing
    a knob closes the gripper on nothing), does not run straight into a hold (the grasp's own closing motion: thin rims
    read < 0.8 cm before the contact flags come on) and a task object is grasped later; long wrong-object contacts are
    brushes (only a wrong grasp is an error); lift/transport credit follows whichever TASK object is held (a wrongly
    grasped object earns nothing) and approach credit goes towards the next object grasped (two-object libero_10
    tasks); chunks during which a fixture joint the task is about moves by >= FIXTURE_CREDIT_DELTA are {progress}
    ("advance_fixture"): any joint when the goal has fixture atoms (open/close/turnon), else the joint of the fixture
    holding the goal region ("open the top drawer and put the bowl inside" has no open atom in LIBERO).
"""
import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/annotate: reuse common.py
from common import PROJ, dump_json, list_datasets, open_dataset, read_episodes_jsonl  # noqa: E402

REFERENCE_VERSION = "r6"
BENCH = Path(os.environ.get("FTL_BENCH", str(PROJ / "bench")))
REF_DIR = BENCH / "references"

LABELS = ("progress", "failure_inducing", "recovery", "neutral", "aftermath")
MODES = ("never_reached", "wrong_object", "missed_grasp", "drop_transport", "release_miss", "hold_no_release",
         "stall_after_grasp", "collision", "other")
MODE_CAUSE = {
    "never_reached": "reaching", "wrong_object": "sequencing_semantic", "missed_grasp": "grasp", "drop_transport": "grasp",
    "release_miss": "manipulation", "hold_no_release": "manipulation", "stall_after_grasp": "manipulation",
    "collision": "collision", "other": "unclear", "success": None,
}

# thresholds (all from the contract unless marked)
DEBOUNCE = 3            # frames of consecutive grasped flag for a hold (and consecutive non-grasped to end it)
HOLD_GAP_FRAMES = 4     # r2: debounced holds of the same slot separated by <= this many frames are one hold
HOLD_MIN_FRAMES = 8     # r2: a (merged) hold shorter than this is ambiguous, not held, unless it is a slip (r3)
SLIP_COLLAPSE_FRAMES = 10  # r3: a short hold ending with cmd CLOSE whose aperture drops < CLOSED_APERTURE within this many frames is a slip
POST_SLIP_FRAMES = 12   # r3: a close-on-nothing run starting within this many frames after a drop is the same failed attempt
ATTEMPT_MIN_DROP = 0.02   # r4: a CLOSE run is a failed grasp attempt when the aperture falls by at least this much ...
ATTEMPT_MAX_MIN = 0.012   # r4: ... to a minimum at or below this (fingers met with nothing, or a sliver, between them)
ATTEMPT_NEAR_XY = 0.05    # r4: without target contact, the eef must be within this xy distance of the target at the minimum
ATTEMPT_AFTER = 2         # r4: the minimum may occur up to this many frames after the command re-opens
TRANSITION = 2          # frames on each side of a hold boundary marked ambiguous
MIN_RUN = 3             # wrong-object contact / collision run length
COLLISION_MODE_FRAMES = 10
IDLE_SPEED = 0.002      # m/frame (episode_progress.py)
IDLE_GRIP = 0.002       # aperture change per frame (episode_progress.py idle definition)
STALL_FRAMES = 40
MIN_FINAL_IDLE = 10     # decision: a final idle run shorter than this does not localise a hold_no_release
CLOSED_APERTURE = 0.008
CLOSE_MIN_FRAMES = 2    # decision
APPROACH_DELTA = 0.02
RECOVERABLE_DIST = 0.25
RECOVERABLE_FRAMES = 40
FIXTURE_EPS = 1e-3
FIXTURE_CREDIT_DELTA = 0.02  # decision (success labels): a fixture joint must move this much to count as task progress
WRONG_LONG = 10         # decision: wrong contact >= this many frames (or a grasp) is an error, shorter is a brush
LOOSE_HOLD_FRAMES = 5   # decision: airborne+contact without grasped flag
GOAL_XY = 0.06          # proxy for target_in_goal (informational only)
GOAL_DZ = 0.15


# ----------------------------------------------------------------------------------------------- primitives
def runs_of(mask):
    """[(start, end_inclusive), ...] of True runs in a 1-D boolean array."""
    mask = np.asarray(mask, bool)
    if mask.size == 0:
        return []
    d = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1) - 1
    return [(int(a), int(b)) for a, b in zip(starts, ends)]


def debounce(raw, k=DEBOUNCE):
    """Hysteresis: the state switches only after >= k consecutive frames of the other value. Starts empty."""
    raw = np.asarray(raw, bool)
    out = np.zeros(raw.shape, bool)
    state = False
    i, n = 0, len(raw)
    while i < n:
        j = i
        while j < n and raw[j] == raw[i]:
            j += 1
        if raw[i] != state and (j - i) >= k:
            state = bool(raw[i])
        out[i:j] = state
        i = j
    return out


def merge_gaps(mask, gap=HOLD_GAP_FRAMES):
    """Fill False gaps of <= gap frames between True runs (two holds separated by a short flag loss are one hold)."""
    mask = np.asarray(mask, bool).copy()
    runs = runs_of(mask)
    for (_, e0), (a1, _) in zip(runs, runs[1:]):
        if a1 - e0 - 1 <= gap:
            mask[e0 + 1:a1] = True
    return mask


def drop_short_runs(mask, min_len=HOLD_MIN_FRAMES):
    """Clear True runs shorter than min_len frames."""
    mask = np.asarray(mask, bool).copy()
    for a, e in runs_of(mask):
        if e - a + 1 < min_len:
            mask[a:e + 1] = False
    return mask


def cmd_open_at(cmd, last_before, first_after):
    """True when an OPEN command (action[6] <= 0) appears in the TRANSITION window around a hold boundary."""
    n = len(cmd)
    lo, hi = max(0, last_before - TRANSITION), min(n - 1, first_after + TRANSITION - 1)
    return bool((np.asarray(cmd)[lo:hi + 1] <= 0).any())


def is_slip(a, e, airborne_col, cmd, grip):
    """r3: a short debounced hold [a, e] is a real hold (a slip) when the object was airborne at some frame of it, or when
    it ended with the command still CLOSE and the aperture fell below CLOSED_APERTURE within SLIP_COLLAPSE_FRAMES frames
    after it (fingers closed on nothing after losing the object). Brushes and finger pushes fail both tests."""
    n = len(cmd)
    if np.asarray(airborne_col, bool)[a:e + 1].any():
        return True
    if e + 1 >= n:
        return False
    still_close = not cmd_open_at(cmd, e, e + 1)
    return still_close and bool((np.asarray(grip)[e + 1:e + 1 + SLIP_COLLAPSE_FRAMES] < CLOSED_APERTURE).any())


def hold_mask(grasped_col, keep_short=None):
    """Hold of one slot: debounced grasped flag, gaps <= HOLD_GAP_FRAMES merged, runs < HOLD_MIN_FRAMES dropped unless
    keep_short(start, end) says the short run is a slip (r3; None = r2 behaviour, every short run dropped)."""
    mask = merge_gaps(debounce(grasped_col))
    for a, e in runs_of(mask):
        if e - a + 1 < HOLD_MIN_FRAMES and not (keep_short is not None and keep_short(a, e)):
            mask[a:e + 1] = False
    return mask


def rle(states, objects):
    """Run-length encode parallel per-frame sequences into [{"start","end","state","object"}]."""
    runs = []
    n = len(states)
    if n == 0:
        return runs
    a = 0
    for i in range(1, n + 1):
        if i == n or states[i] != states[a] or objects[i] != objects[a]:
            runs.append({"start": a, "end": i - 1, "state": states[a], "object": objects[a]})
            a = i
    return runs


def expand_runs(runs, n):
    """Inverse of rle for held_runs: per-frame (state, object) lists."""
    states, objects = [None] * n, [None] * n
    for r in runs:
        for i in range(r["start"], r["end"] + 1):
            states[i], objects[i] = r["state"], r["object"]
    return states, objects


def _chunk_of(chunks, i):
    for c, (a, b) in enumerate(chunks):
        if a <= i < b:
            return c
    return len(chunks) - 1


def slot_for_region(region, slots):
    """Object slot owning a goal region name ('basket_1_contain_region' -> 'basket_1'); None for fixture regions."""
    if region in slots:
        return region
    cands = [s for s in slots if region.startswith(s + "_")]
    return max(cands, key=len) if cands else None


def resolve_targets(meta, target_mask):
    """Movable target objects and their goals from goal_state; fallback to the slot-ordered target_mask."""
    slots = list(meta.get("object_slots", []))
    atoms = meta.get("goal_state") or []
    movable, goal_of, fixture_atoms = [], {}, []
    for atom in atoms:
        atom = [str(x) for x in atom]
        if atom and atom[0].lower() in ("on", "in") and len(atom) >= 3 and atom[1] in slots:
            if atom[1] not in movable:
                movable.append(atom[1])
            goal_of[atom[1]] = (slot_for_region(atom[2], slots), atom[2])
        else:
            fixture_atoms.append(atom)
    selection = "goal_state"
    if not movable:
        masked = [slots[i] for i in np.flatnonzero(target_mask[: len(slots)])]
        if masked and not atoms:  # old schema without goal_state: episode_progress convention
            movable = [masked[0]]
            goal_of[masked[0]] = (masked[1] if len(masked) > 1 else None, masked[1] if len(masked) > 1 else None)
            selection = "mask_fallback"
        else:
            selection = "fixture_only" if atoms else "none"
    return {"slots": slots, "movable": movable, "goal_of": goal_of, "fixture_atoms": fixture_atoms, "selection": selection}


# ----------------------------------------------------------------------------------------------- main builder
def build_reference(ep):
    """Reference dict for one episode (common.Episode or any object with the same column/chunk interface)."""
    n, chunks = int(ep.n), list(ep.chunks)
    meta = ep.meta
    cof = lambda i: _chunk_of(chunks, int(i))  # noqa: E731

    tmask = np.asarray(ep.col("priv.target_mask")[0]).reshape(-1) > 0
    tg = resolve_targets(meta, tmask)
    slots = tg["slots"]
    S = len(slots)
    valid = np.asarray(ep.col("priv.obj_valid")[0]).reshape(-1)[:S] > 0 if S else np.zeros(0, bool)
    b = lambda k: np.asarray(ep.col(k))[:, :S] > 0  # noqa: E731
    gcon, lf, rf, grasped = b("priv.obj_gripper_contact"), b("priv.obj_left_finger_contact"), b("priv.obj_right_finger_contact"), b("priv.obj_grasped")
    sup, oo, resting = b("priv.obj_support_contact"), b("priv.obj_obj_contact"), b("priv.obj_resting")
    pos = np.asarray(ep.col("priv.obj_pos"), np.float64).reshape(n, -1, 3)[:, :S]
    arm = np.asarray(ep.col("priv.arm_contacts")).reshape(-1) > 0
    gstat = np.asarray(ep.col("priv.gripper_static_contacts")).reshape(-1) > 0
    gfix = np.asarray(ep.col("priv.gripper_fixture_contacts")).reshape(-1) > 0
    fq = np.asarray(ep.col("priv.fixture_qpos"), np.float64)
    fvalid = np.asarray(ep.col("priv.fixture_valid")[0]).reshape(-1) > 0
    eef = np.asarray(ep.col("priv.eef_pos"), np.float64)
    grip = np.asarray(ep.gripper_aperture, np.float64)
    cmd = np.asarray(ep.gripper_cmd, np.float64)
    succ = np.asarray(ep.col("next.success")).reshape(-1) > 0
    for arr in (gcon, lf, rf, grasped, sup, oo, resting):
        arr[:, ~valid] = False
    anomalies = []

    # --- held state (contract: obj_grasped debounced, r2: gaps merged and short holds dropped, r3: short holds kept
    #     when they are slips; ambiguity rules in the module docstring). deb = raw debounced flag (loose-hold anomaly
    #     check), hold = what counts as held.
    deb = np.zeros((n, S), bool)
    hold = np.zeros((n, S), bool)
    air_all = (~sup) & (~oo)  # per slot: no support contact and no object-object contact
    for s in range(S):
        deb[:, s] = debounce(grasped[:, s])
        hold[:, s] = hold_mask(grasped[:, s], keep_short=lambda a, e, s=s: is_slip(a, e, air_all[:, s], cmd, grip))
    movable_idx = [slots.index(o) for o in tg["movable"]]
    # active target: single movable target, else the one held longest, else contacted longest, else first atom
    if len(movable_idx) == 1:
        t, tsel = movable_idx[0], "single"
    elif len(movable_idx) > 1:
        held_frames = [int(hold[:, s].sum()) for s in movable_idx]
        con_frames = [int(gcon[:, s].sum()) for s in movable_idx]
        if max(held_frames) > 0:
            t, tsel = movable_idx[int(np.argmax(held_frames))], "most_held"
        elif max(con_frames) > 0:
            t, tsel = movable_idx[int(np.argmax(con_frames))], "most_contact"
        else:
            t, tsel = movable_idx[0], "first_atom"
    else:
        t, tsel = None, tg["selection"]
    goal_slot, goal_region = (tg["goal_of"].get(slots[t], (None, None)) if t is not None else (None, None))
    g = slots.index(goal_slot) if goal_slot in slots else None
    multi_target = len(movable_idx) > 1
    fixture_atoms = tg["fixture_atoms"]

    held_slot = np.full(n, -1, int)
    for s in range(S - 1, -1, -1):  # lowest index wins, target overrides
        held_slot[hold[:, s]] = s
    if t is not None:
        held_slot[hold[:, t]] = t
    transition = np.zeros(n, bool)
    amb_obj = np.full(n, -1, int)
    slot_runs = {s: runs_of(hold[:, s]) for s in range(S)}
    for s in range(S):
        for a, e in slot_runs[s]:
            for i in range(max(0, a - TRANSITION), min(n, a + TRANSITION)):
                transition[i] = True
                amb_obj[i] = s if amb_obj[i] < 0 else amb_obj[i]
            for i in range(max(0, e - TRANSITION + 1), min(n, e + TRANSITION + 1)):
                transition[i] = True
                amb_obj[i] = s if amb_obj[i] < 0 else amb_obj[i]
    xor = lf ^ rf
    xor_any = xor.any(1) if S else np.zeros(n, bool)
    blip = (grasped.any(1) | deb.any(1)) & (held_slot < 0) if S else np.zeros(n, bool)  # blips and short holds
    states, objects = [], []
    for i in range(n):
        s = held_slot[i]
        if s >= 0:
            states.append("held" if (grasped[i, s] and not transition[i]) else "ambiguous")  # merged gaps -> ambiguous
            objects.append(slots[s])
        elif transition[i] or xor_any[i] or blip[i]:
            states.append("ambiguous")
            o = amb_obj[i]
            if o < 0:
                cands = np.flatnonzero(grasped[i] | deb[i] | xor[i]) if S else []
                o = int(cands[0]) if len(cands) else -1
            objects.append(slots[o] if o >= 0 else None)
        else:
            states.append("empty")
            objects.append(None)
    held_runs = rle(states, objects)

    # --- events: transitions of the combined debounced held object -----------------------------------------------
    def cmd_open(last_before, first_after):
        return cmd_open_at(cmd, last_before, first_after)

    events = []
    held_at_end = lambda last: last >= n - 1 - DEBOUNCE  # noqa: E731  hold ends within DEBOUNCE frames of the end
    for a, e in runs_of(held_slot >= 0):
        # split at object changes
        seg_start = a
        for i in range(a + 1, e + 2):
            if i > e or held_slot[i] != held_slot[seg_start]:
                s = int(held_slot[seg_start])
                sa, se = seg_start, i - 1
                hold_frames = se - sa + 1  # length of the hold this event starts/ends
                if sa > 0:
                    events.append({"index": sa, "type": "grasp", "object": slots[s], "last_before": sa - 1, "first_after": sa,
                                   "chunk": cof(sa - 1), "gripper_cmd_open": cmd_open(sa - 1, sa), "hold_frames": hold_frames})
                else:
                    anomalies.append("held_at_frame_0")
                if not held_at_end(se):
                    op = cmd_open(se, se + 1)
                    events.append({"index": se + 1, "type": "release" if op else "drop", "object": slots[s], "last_before": se,
                                   "first_after": se + 1, "chunk": cof(se), "gripper_cmd_open": op, "hold_frames": hold_frames})
                seg_start = i
    events.sort(key=lambda ev: (ev["index"], ev["type"] != "grasp"))

    # --- other privileged facts ---------------------------------------------------------------------------------
    wrong = []
    for s in range(S):
        if tmask[s] or not valid[s]:
            continue
        for a, e in runs_of(gcon[:, s]):
            if e - a + 1 >= MIN_RUN:
                wrong.append({"object": slots[s], "start": a, "end": e, "grasped": bool(deb[a:e + 1, s].any()), "chunk": cof(a)})
    wrong.sort(key=lambda w: w["start"])
    collisions = [{"start": a, "end": e, "chunk": cof(a)} for a, e in runs_of(arm) if e - a + 1 >= MIN_RUN]
    fixture_motion = []
    jnames = list(meta.get("fixture_joint_names", []))
    for j in range(min(fq.shape[1], len(fvalid))):
        if not fvalid[j]:
            continue
        q = fq[:, j]
        if q.max() - q.min() > FIXTURE_EPS:
            moved = np.abs(q - q[0]) > FIXTURE_EPS
            a = int(np.argmax(moved))
            steps = np.flatnonzero(np.abs(np.diff(q)) > 1e-5)
            e = int(steps[-1] + 1) if len(steps) else a
            fixture_motion.append({"joint": jnames[j] if j < len(jnames) else f"joint_{j}", "start": a, "end": e,
                                   "delta": float(q[e] - q[max(a - 1, 0)])})
    closed = (cmd > 0) & (grip < CLOSED_APERTURE) & (held_slot < 0) & (~gcon.any(1) if S else True)
    close_on_nothing = [{"start": a, "end": e, "chunk": cof(a)} for a, e in runs_of(closed) if e - a + 1 >= CLOSE_MIN_FRAMES]
    # r3: a closure that begins within POST_SLIP_FRAMES after a drop is the empty gripper finishing the closing motion of
    # the attempt that just lost the object: same failed attempt, no error of its own (kept apart for transparency)
    drop_ends = [ev["last_before"] for ev in events if ev["type"] == "drop"]
    post_slip_closure = []
    for c in close_on_nothing:
        after = [e for e in drop_ends if 0 < c["start"] - e <= POST_SLIP_FRAMES]
        if after:
            post_slip_closure.append(dict(c, after_drop=int(max(after))))
    close_on_nothing = [c for c in close_on_nothing if not any(p["start"] == c["start"] for p in post_slip_closure)]

    # r4: failed grasp attempts. This policy re-opens the instant the fingers meet, so a miss almost never sits closed
    # for CLOSE_MIN_FRAMES; the closing MOTION itself is the evidence: a CLOSE run without any hold in which the aperture
    # collapses (>= ATTEMPT_MIN_DROP down to <= ATTEMPT_MAX_MIN) while the gripper touched the target or was next to it.
    attempts = []
    if t is not None:
        tgt_touch = gcon[:, t] | lf[:, t] | rf[:, t]
        # only an articulated-fixture contact (knob, handle) disqualifies a run; a fingertip brushing the table (static
        # geom) while closing on the object is part of a normal failed attempt
        for a, e in runs_of(cmd > 0):
            if e - a + 1 < 3 or (held_slot[a:e + 1] >= 0).any() or gfix[a:e + 1].any():
                continue
            e2 = min(n - 1, e + ATTEMPT_AFTER)
            seg = grip[a:e2 + 1]
            k = int(np.argmin(seg))
            fmin = min(a + k, e)  # the attempt ends with the CLOSE command even if the fingers are still travelling
            if grip[a] - seg[k] < ATTEMPT_MIN_DROP or seg[k] > ATTEMPT_MAX_MIN:
                continue
            touch = tgt_touch[a:fmin + 1]
            near = float(np.linalg.norm(eef[fmin, :2] - pos[fmin, t, :2])) <= ATTEMPT_NEAR_XY
            if not (touch.any() or near):
                continue
            f0 = a + int(np.argmax(touch)) if touch.any() else int(a)
            attempts.append({"index": len(attempts), "start": int(f0), "end": int(fmin), "chunk": cof(f0),
                             "chunks": sorted({cof(f) for f in range(f0, fmin + 1)}), "contact": bool(touch.any()),
                             "min_aperture_m": float(seg[k])})
    if attempts:
        # a closed-empty run inside or shortly after an attempt is the same failed attempt; each chunk the attempt spans
        # gets a failed-closure record so the chunk rules mark all of them
        close_on_nothing = [c for c in close_on_nothing
                            if not any(x["start"] <= c["start"] <= x["end"] + POST_SLIP_FRAMES for x in attempts)]
        for x in attempts:
            for ch in x["chunks"]:
                close_on_nothing.append({"start": int(max(x["start"], chunks[ch][0])), "end": int(x["end"]), "chunk": int(ch),
                                         "kind": "attempt", "attempt": x["index"]})
        close_on_nothing.sort(key=lambda c: (c["start"], c["chunk"]))

    # --- stage frames: rules of scripts/analysis/episode_progress.py (analyze_episode), reproduced verbatim -------
    speed = np.linalg.norm(np.diff(eef, axis=0), axis=1)
    dgrip = np.abs(np.diff(grip))
    idle = (speed < IDLE_SPEED) & (dgrip < IDLE_GRIP)  # idle[i]: no motion between frame i and i+1
    placed_f = int(np.argmax(succ)) if succ.any() else -1
    if t is not None:
        gc_t, gr_t, sup_t, oo_t = gcon[:, t], grasped[:, t], sup[:, t], oo[:, t]
        airborne = (~sup_t) & (~oo_t)
        held_p = gr_t | (gc_t & airborne)  # episode_progress "held": both-pad grasp OR (contact AND airborne)
        reached_f = int(np.argmax(gc_t)) if gc_t.any() else (int(np.argmax(gstat)) if gstat.any() else -1)
        grasped_f = int(np.argmax(held_p)) if held_p.any() else -1
        lifted_f = int(np.argmax(held_p & airborne)) if (held_p & airborne).any() else -1
        xy0 = pos[0, t, :2]
        disp = np.linalg.norm(pos[:, t, :2] - xy0, axis=1)
        if g is not None:
            d_goal = np.linalg.norm(pos[:, t, :2] - pos[:, g, :2], axis=1)
            transported = (d_goal <= 0.12) & (disp > 0.05)
        else:
            d_goal = None
            transported = disp >= 0.15
        transported_f = int(np.argmax(transported)) if transported.any() else -1
    else:
        airborne = np.zeros(n, bool)
        touch = gfix | gstat
        reached_f = int(np.argmax(touch)) if touch.any() else -1
        grasped_f = lifted_f = transported_f = -1
        d_goal, disp = None, np.zeros(n)
    stage_frames = {"reached": reached_f, "grasped": grasped_f, "lifted": lifted_f, "transported": transported_f, "placed": placed_f}

    # --- final state -------------------------------------------------------------------------------------------
    if t is not None:
        dxy = float(d_goal[-1]) if d_goal is not None else None
        final = {
            "target_in_goal": bool(placed_f >= 0 or (dxy is not None and dxy <= GOAL_XY and resting[-1, t] and abs(pos[-1, t, 2] - pos[-1, g, 2]) <= GOAL_DZ)),
            "target_in_goal_predicate": bool(placed_f >= 0),
            "target_resting": bool(resting[-1, t]), "target_dist_to_goal_xy_m": dxy,
            "target_z_m": float(pos[-1, t, 2]), "target_moved_m": float(np.linalg.norm(pos[-1, t] - pos[0, t])),
        }
    else:
        final = {"target_in_goal": bool(placed_f >= 0), "target_in_goal_predicate": bool(placed_f >= 0), "target_resting": None,
                 "target_dist_to_goal_xy_m": None, "target_z_m": None, "target_moved_m": None}

    # --- failure mode ---------------------------------------------------------------------------------------------
    target_runs = slot_runs[t] if t is not None else []
    target_events = [ev for ev in events if t is not None and ev["object"] == slots[t]]
    first_contact = int(np.argmax(gcon[:, t])) if (t is not None and gcon[:, t].any()) else None
    loose = (gcon[:, t] & airborne & ~deb[:, t]) if t is not None else np.zeros(n, bool)
    loose_runs = [(a, e) for a, e in runs_of(loose) if e - a + 1 >= LOOSE_HOLD_FRAMES]
    if loose_runs:
        anomalies.append(f"airborne_contact_without_grasp_flag:{len(loose_runs)}runs,max{max(e - a + 1 for a, e in loose_runs)}f")
    final_idle_start = None
    if len(idle) and idle[-1]:
        a = runs_of(idle)[-1][0]
        if n - a >= MIN_FINAL_IDLE:
            final_idle_start = int(a)

    mode, D, first_error, reason = None, None, None, ""
    if ep.success:
        mode, reason = "success", "success"
    elif t is None:
        if not (gfix | gstat).any() and not wrong:
            mode, reason = "never_reached", "fixture_task_no_contact"
        else:
            mode, reason = "other", f"fixture_only_task:{tg['selection']}"
    else:
        # wrong-object evidence before the first target contact: a debounced grasp of the wrong object, or a contact of
        # >= WRONG_LONG frames while the target is never held. A shorter brush never decides the mode by itself (it
        # stays visible as a "wrong_contact_brush" chunk); in the data 161/197 wrong_object episodes have a wrong grasp.
        early_wrong = [w for w in wrong if first_contact is None or w["start"] < first_contact]
        early_grasp = [w for w in early_wrong if w["grasped"]]
        early_long = [w for w in early_wrong if w["end"] - w["start"] + 1 >= WRONG_LONG]
        if early_grasp or (early_long and not target_runs):
            w = early_grasp[0] if early_grasp else early_long[0]
            w = min([w] + [x for x in early_wrong if x["start"] <= w["start"]], key=lambda x: x["start"])
            mode, D, first_error = "wrong_object", w["chunk"], w["start"]
            reason = "wrong_grasp_before_target" if early_grasp else "wrong_contact_no_target_hold"
        elif first_contact is None and not (early_grasp or early_long):
            mode, reason = "never_reached", "no_target_contact" + ("_brushed_wrong_object" if wrong else "")
        elif loose_runs:
            mode, reason = "other", "airborne_contact_without_grasp_flag"
        elif target_runs:
            a, e = target_runs[-1]
            lifted_by_end = {re: bool(airborne[ra:re + 1].any()) for ra, re in target_runs}
            # A hold that never lifted the object (support contact throughout) and ended is a failed grasp attempt
            # (fingers closed on the object, it slipped out / was let go on the table): a "failed closure", like a
            # close-on-nothing. In the data these holds last 3-15 frames with < 1-3 cm of z rise.
            end_evs = [ev for ev in target_events if ev["type"] != "grasp"]
            lifted_drops = [ev for ev in end_evs if ev["type"] == "drop" and lifted_by_end[ev["last_before"]]]
            failed_closures = sorted([(ev["last_before"], ev["chunk"], "slip_" + ev["type"]) for ev in end_evs if not lifted_by_end[ev["last_before"]]]
                                     + [(c["start"], c["chunk"], "close_on_nothing") for c in close_on_nothing if c["start"] >= first_contact])
            if held_at_end(e):
                # r2: held at the end (within DEBOUNCE frames of it) is always hold_no_release / stall_after_grasp, whatever
                # happened before; the final carry is not "aftermath" of an earlier drop (r1 blamed the last prior error).
                near_goal = transported_f >= 0 or (d_goal is not None and d_goal[-1] <= 0.12)
                hold_len = n - a
                prior = "_after_drop" if any(ev["last_before"] < a for ev in lifted_drops) else ""
                if final_idle_start is not None:
                    idle_len = n - final_idle_start
                    if idle_len >= STALL_FRAMES and not near_goal:
                        mode, reason = "stall_after_grasp", f"held_at_end_idle{idle_len}_far_from_goal"
                    else:
                        mode, reason = "hold_no_release", f"held_at_end_idle{idle_len}" + ("_near_goal" if near_goal else "")
                    D, first_error = cof(final_idle_start), final_idle_start
                else:
                    # still moving with the object when time runs out: no "chunk where motion stops", decisive_chunk null
                    mode, reason = "hold_no_release", f"active_hold{hold_len}_no_idle" + ("_near_goal" if near_goal else "")
                reason += prior
            else:
                end_ev = [ev for ev in end_evs if ev["last_before"] == e][0]
                lifted_in_run = lifted_by_end[e]
                if not lifted_in_run:
                    fc = failed_closures[0]
                    mode, D, first_error, reason = "missed_grasp", fc[1], fc[0], f"last_hold_{end_ev['type']}_without_lift;first_failed_closure={fc[2]}"
                elif end_ev["type"] == "drop":
                    mode, D, first_error, reason = "drop_transport", end_ev["chunk"], e, "last_hold_ends_in_drop"
                elif multi_target:
                    mode, reason = "other", "multi_target_release_unresolved"
                elif fixture_atoms:
                    mode, reason = "other", "fixture_atom_release_unresolved:" + ",".join("/".join(x) for x in fixture_atoms)
                else:
                    mode, D, first_error, reason = "release_miss", end_ev["chunk"], e, "last_hold_ends_in_release"
        else:
            cons = [c for c in close_on_nothing if c["start"] >= first_contact]
            mode = "missed_grasp"
            if cons:
                D, first_error, reason = cons[0]["chunk"], cons[0]["start"], "contact_then_close_on_nothing"
            else:
                first_error, reason = first_contact, "contact_never_held_no_close_on_nothing"
        # collision override: arm contact >= 10 frames that precedes the first other error
        long_coll = [c for c in collisions if c["end"] - c["start"] + 1 >= COLLISION_MODE_FRAMES]
        if long_coll and mode != "success" and (first_error is None or long_coll[0]["start"] < first_error):
            reason = f"collision_precedes_{mode}({reason})"
            mode, D, first_error = "collision", long_coll[0]["chunk"], long_coll[0]["start"]
    cause = MODE_CAUSE[mode]

    # --- chunk labels ------------------------------------------------------------------------------------------
    is_success = mode == "success"
    succ_f = placed_f if placed_f >= 0 else n  # frame whose action first satisfies the predicate (n: never)
    movable_names = set(tg["movable"])
    dec_boundary = None
    if D is not None and mode in ("drop_transport", "release_miss", "missed_grasp"):
        evs_d = [x for x in target_events if x["chunk"] == D and x["type"] != "grasp" and x["last_before"] == first_error]
        if evs_d and cof(evs_d[-1]["first_after"]) != D:
            dec_boundary = cof(evs_d[-1]["first_after"])
    err_types = ("drop", "release", "close_on_nothing", "wrong_grasp")
    if is_success:
        # a close-on-nothing is a recovered miss only when the closed gripper touches no fixture (knob, handle), the
        # closure does not run straight into a hold (the grasp's own closing motion, thin rims read < 0.8 cm before the
        # contact flags come on) and a task object is grasped later
        touch_fix = gfix | gstat
        grasp_starts = [ev["first_after"] for ev in events if ev["type"] == "grasp" and ev["object"] in movable_names]

        def is_miss(x):
            later = [f for f in grasp_starts if f > x["end"]]
            return bool(later) and min(later) > x["end"] + 1 + HOLD_GAP_FRAMES and not touch_fix[x["start"]:x["end"] + 1].any()

        cons_err = [x for x in close_on_nothing if is_miss(x)]
    else:
        cons_err = close_on_nothing
    def final_for(ev):
        """A drop/release after which the same object is never grasped again (success: the placement)."""
        return not any(e["type"] == "grasp" and e["index"] > ev["index"] and e["object"] == ev["object"] for e in events)

    def timeline_type(ev):
        # success: the final drop/release of a task object is its placement, not an error the robot recovers from
        if is_success and ev["type"] != "grasp" and ev["object"] in movable_names and final_for(ev):
            return "place"
        return ev["type"]

    timeline = [(ev["index"], timeline_type(ev), ev["object"]) for ev in events]
    timeline += [(x["start"], "close_on_nothing", None) for x in cons_err]
    timeline += [(w["start"], "wrong_grasp" if w["grasped"] else "wrong_contact", w["object"]) for w in wrong]
    timeline.sort()
    onsets = {}
    for k in ("reached", "grasped", "lifted", "transported"):
        if stage_frames[k] >= 0:
            onsets.setdefault(stage_frames[k], []).append(k)
    if is_success and placed_f >= 0:
        onsets.setdefault(placed_f, []).append("placed")
    for ev in events:
        if ev["type"] == "grasp":
            onsets.setdefault(ev["first_after"], []).append("hold")
    if first_contact is not None:
        onsets.setdefault(first_contact, []).append("contact")
    dist_t = np.linalg.norm(eef - pos[:, t], axis=1) if t is not None else None
    goal_idx = {slots.index(o): slots.index(gs) for o, (gs, _) in tg["goal_of"].items() if gs in slots}
    # success: fixture motion that the task asks for (an open/close/turnon atom, or the goal region is inside the moving
    # fixture: wooden_cabinet_1_top_level vs wooden_cabinet_1_top_region); 1-2 mm jitters of other joints do not count
    fix_prefix = lambda s: str(s).rsplit("_", 1)[0]  # noqa: E731
    task_fixture_motion = [m for m in fixture_motion if is_success and abs(m["delta"]) >= FIXTURE_CREDIT_DELTA
                           and (fixture_atoms or (g is None and goal_region and fix_prefix(m["joint"]) == fix_prefix(goal_region)))]
    _dist_cache = {}

    # Evaluate acquisition over the complete hold, rather than rewarding its onset
    # before a short slip in the next chunk is examined. Preserve credit for a
    # sustained airborne carry even if it eventually drops during transport.
    failed_grasp_attempts = []
    for ev in events:
        if ev["type"] != "grasp" or ev["object"] not in movable_names:
            continue
        end = next((x for x in events if x["object"] == ev["object"]
                    and x["type"] != "grasp" and x["index"] > ev["index"]), None)
        if end is None or (is_success and final_for(end)):
            continue
        s = slots.index(ev["object"])
        a, b = ev["first_after"], end["last_before"]
        lifted = ((~sup[a:b + 1, s]) & (~oo[a:b + 1, s])).any()
        if not lifted or (end["type"] == "drop" and b - a + 1 < HOLD_MIN_FRAMES):
            failed_grasp_attempts.append({"start": ev["last_before"], "end": b,
                                          "object": ev["object"], "end_chunk": end["chunk"]})

    def dist_to(s):
        if s not in _dist_cache:
            _dist_cache[s] = np.linalg.norm(eef - pos[:, s], axis=1)
        return _dist_cache[s]

    def pre_label(c, c0, c1, evs, cons_c, wrong_c, grasp_c, earlier_err, later_grasp, last_before_chunk):
        """Allowed set and rule of a chunk before the decisive chunk (and of every pre-success chunk)."""
        in_c = lambda f: c0 <= f < c1  # noqa: E731
        drops = [ev for ev in evs if ev["type"] == "drop"]
        rels = [ev for ev in evs if ev["type"] == "release"]
        if is_success:
            err_drops = [ev for ev in drops if not final_for(ev)]
            final_drops = [ev for ev in drops if ev["object"] in movable_names and final_for(ev)]
            wrong_err = any(w["grasped"] for w in wrong_c)
        else:
            err_drops, final_drops = drops, []
            wrong_err = any(w["grasped"] or w["end"] - w["start"] + 1 >= WRONG_LONG for w in wrong_c)
        if grasp_c and earlier_err:
            return ["recovery"], "regrasp"
        if err_drops or cons_c or wrong_err:
            return ["failure_inducing"], "other_event"
        if rels:
            if is_success and all(ev["object"] in movable_names and final_for(ev) for ev in rels):
                return ["progress"], "place_release"
            if is_success and all(ev["object"] not in movable_names for ev in rels):
                return ["recovery", "neutral", "progress"], "wrong_release"  # putting a wrongly grasped object back down
            return ["failure_inducing", "neutral", "progress"], "other_release"
        if final_drops:  # a task object dropped and never re-grasped: it landed where the task wanted it (or was pushed in)
            return ["progress", "neutral"], "drop_final"
        if wrong_c:
            return ["failure_inducing", "progress", "neutral"], "wrong_contact_brush"
        # causal window of chunk c: its actions produce the motions c0->c0+1 ... c1-1->c1
        adv = [k for f, ks in onsets.items() if in_c(f) or f == c1 for k in ks]
        cz = min(c1, n - 1)
        held_c = (held_slot[c0:c1] >= 0).all()
        empty_c = (held_slot[c0:c1] < 0).all()
        if not adv and t is not None:
            if is_success:
                # credit follows the TASK object in hand / the next task object to be grasped (two-object tasks); a
                # wrongly grasped object earns nothing for being lifted
                s_h = int(held_slot[c0]) if held_c and (held_slot[c0:c1] == held_slot[c0]).all() else None
                if s_h is not None and slots[s_h] not in movable_names:
                    s_h = None
                nxt = [slots.index(o) for f, ty, o in timeline if ty == "grasp" and f >= c1 and o in movable_names] or [t]
                if empty_c and any(dist_to(s)[c0] - dist_to(s)[cz] >= APPROACH_DELTA for s in nxt):
                    adv.append("approach")
                if s_h is not None and s_h in goal_idx:
                    dg = np.linalg.norm(pos[:, s_h, :2] - pos[:, goal_idx[s_h], :2], axis=1)
                    if dg[c0] - dg[cz] >= APPROACH_DELTA:
                        adv.append("transporting")
                if s_h is not None and pos[cz, s_h, 2] - pos[c0, s_h, 2] >= APPROACH_DELTA:
                    adv.append("lifting")
            else:
                if empty_c and dist_t[c0] - dist_t[cz] >= APPROACH_DELTA:
                    adv.append("approach")
                if held_c and d_goal is not None and d_goal[c0] - d_goal[cz] >= APPROACH_DELTA:
                    adv.append("transporting")
                if held_c and pos[cz, t, 2] - pos[c0, t, 2] >= APPROACH_DELTA:
                    adv.append("lifting")
        if not adv and any(m["start"] - 1 < c1 and m["end"] >= c0 for m in task_fixture_motion):
            adv.append("fixture")  # the fixture the task is about is moving (success only, see task_fixture_motion)
        if adv:
            if earlier_err and empty_c and set(adv) <= {"approach", "contact", "reached"}:
                return ["neutral"], "retry_motion"
            return ["progress"], "advance_" + "+".join(sorted(set(adv)))
        if idle[c0:min(c1, n - 1)].all():
            return ["neutral"], "idle"
        if last_before_chunk and last_before_chunk[-1] in err_types and later_grasp:
            return ["neutral"], "pre_recovering"
        return ["progress", "neutral"], "pre_other"

    # r3: decisive null but the events are known -> labels from the events (pre-decisive rules over the whole episode);
    # the final hold of a held-at-end episode gets "final_hold_active" where it is neither an advance nor idle
    event_labelled = (not is_success and D is None and mode != "never_reached" and bool(target_events)
                      and not reason.startswith("airborne_contact_without_grasp_flag"))
    final_hold = target_runs[-1] if (target_runs and held_at_end(target_runs[-1][1])) else None

    chunk_labels = []
    for c, (c0, c1) in enumerate(chunks):
        allowed, rule, scorable = None, None, True
        evs = [ev for ev in events if ev["chunk"] == c]
        cons_c = [x for x in cons_err if x["chunk"] == c]
        wrong_c = [w for w in wrong if w["chunk"] == c]
        grasp_c = [ev for ev in evs if ev["type"] == "grasp" and (t is None or ev["object"] == slots[t] or (is_success and ev["object"] in movable_names))]
        earlier_err = any(f < c0 and ty in err_types for f, ty, _ in timeline)
        later_grasp = any(f >= c1 and ty == "grasp" for f, ty, _ in timeline)
        last_before_chunk = [ty for f, ty, _ in timeline if f < c0]
        pre_args = (c, c0, c1, evs, cons_c, wrong_c, grasp_c, earlier_err, later_grasp, last_before_chunk)
        if mode == "never_reached":
            allowed, rule, scorable = ["failure_inducing", "neutral", "progress"], "unlocalised", False
        elif is_success:
            if c0 > succ_f:
                allowed, rule = ["neutral", "aftermath"], "post_success"
            else:
                allowed, rule = pre_label(*pre_args)
        elif event_labelled:
            allowed, rule = pre_label(*pre_args)
            if final_hold is not None and rule == "pre_other" and c0 <= final_hold[1] and c1 > final_hold[0]:
                rule = "final_hold_active"  # carrying / manoeuvring with the object when time ran out
        elif mode == "other" or D is None:
            allowed, rule, scorable = list(LABELS), f"unlocalised_{mode}", False
        elif c == D:
            allowed, rule = ["failure_inducing"], "decisive"
        elif c < D:
            allowed, rule = pre_label(*pre_args)
            if mode == "wrong_object" and "failure_inducing" not in allowed:
                allowed, rule = allowed + ["failure_inducing"], rule + "+wrong_approach"
        else:
            if grasp_c:
                allowed, rule = ["recovery"], "regrasp"
            elif any(x.get("kind") == "attempt" for x in cons_c):
                allowed, rule = ["failure_inducing"], "attempt"  # r4: the same failed attempt continues past the decisive chunk
            elif any(ev["type"] == "drop" for ev in evs) or cons_c or any(w["grasped"] for w in wrong_c):
                allowed, rule = ["failure_inducing", "aftermath", "recovery"], "post_event"
            elif t is not None and (held_slot[c0:c1] == t).any():
                # r2: the target is (still or again) held after the decisive chunk; the oracle cannot judge a late carry
                allowed, rule = ["progress", "recovery", "neutral", "aftermath"], "post_held_unscorable"
            elif t is not None and dist_t[c0:c1].min() <= RECOVERABLE_DIST and n - c0 >= RECOVERABLE_FRAMES:
                allowed, rule = ["neutral", "aftermath", "recovery"], "post_recoverable"
            else:
                allowed, rule = ["aftermath", "neutral"], "post_other"
            if mode == "collision" and "progress" not in allowed:
                allowed, rule = allowed + ["progress"], rule + "+post_collision"
        if dec_boundary is not None and c == dec_boundary and "failure_inducing" not in allowed:
            allowed, rule = allowed + ["failure_inducing"], rule + "+decisive_boundary"
        # r5: a chunk can contain both a recovery grasp and a renewed error. Do not
        # let branch precedence turn that mixed evidence into certain positive credit.
        other_local_error = (any(ev["type"] == "drop" and (not is_success or not final_for(ev)) for ev in evs)
                             or any(w["grasped"] for w in wrong_c))
        local_error = other_local_error or bool(cons_c)
        if scorable and grasp_c and local_error:
            allowed, rule = ["failure_inducing", "neutral"], "mixed_event"
        elif scorable and cons_c and all(x.get("kind") == "attempt" for x in cons_c):
            # Only a chunk fully covered by failed closing motion gets a singleton
            # attempt label. Partial overlap does not identify the sign of all actions.
            covered = np.zeros(c1 - c0, bool)
            for x in cons_c:
                attempt = attempts[x["attempt"]]
                covered[max(c0, attempt["start"]) - c0:min(c1, attempt["end"] + 1) - c0] = True
            if not covered.all() and not other_local_error:
                allowed, rule = ["failure_inducing", "neutral"], "attempt_boundary"
        failed_acquisition = [x for x in failed_grasp_attempts if x["start"] < c1 and x["end"] >= c0]
        if scorable and failed_acquisition:
            if any(x["end_chunk"] == c for x in failed_acquisition):
                allowed, rule = ["failure_inducing"], "decisive" if c == D and not is_success else "failed_acquisition"
            else:
                allowed, rule = ["failure_inducing", "neutral"], "failed_acquisition_boundary"
        primary = {"decisive": "failure_inducing", "attempt": "failure_inducing", "regrasp": "recovery", "other_event": "failure_inducing", "other_release": "failure_inducing",
                   "failed_acquisition": "failure_inducing", "failed_acquisition_boundary": "neutral", "retry_motion": "neutral",
                   "mixed_event": "failure_inducing", "attempt_boundary": "neutral",
                   "wrong_contact_brush": "progress", "pre_recovering": "neutral", "idle": "neutral", "pre_other": "progress",
                   "post_event": "aftermath", "post_recoverable": "aftermath", "post_other": "aftermath", "post_held_unscorable": "neutral",
                   "unlocalised": "neutral", "post_success": "neutral", "place_release": "progress", "drop_final": "progress",
                   "wrong_release": "recovery", "final_hold_active": "progress"}.get(rule.split("+")[0], "progress" if rule.startswith("advance") else "neutral")
        chunk_labels.append({"chunk": c, "allowed": allowed, "primary": primary, "rule": rule, "scorable": scorable})

    if is_success:
        # landmarks of a success: only a recovered error (first drop / close-on-nothing / wrong grasp that was followed by a
        # later grasp) gives a decisive chunk and a cause; otherwise both stay null / unclear
        recovered = [cl["chunk"] for cl in chunk_labels if cl["rule"].split("+")[0] in ("other_event", "mixed_event", "attempt_boundary", "failed_acquisition")]
        if recovered:
            D = recovered[0]
            kinds = [(ev["last_before"], "drop") for ev in events if ev["type"] == "drop" and ev["chunk"] == D]
            kinds += [(x["start"], "close_on_nothing") for x in cons_err if x["chunk"] == D]
            kinds += [(w["start"], "wrong_grasp") for w in wrong if w["grasped"] and w["chunk"] == D]
            first_error, kind = min(kinds) if kinds else (chunks[D][0], "drop")
            cause = {"drop": "grasp", "close_on_nothing": "grasp", "wrong_grasp": "sequencing_semantic"}[kind]
            reason = f"success_recovered_{kind}"
        else:
            cause = "unclear"
        if placed_f < 0:
            anomalies.append("success_without_predicate")
        elif t is not None and not target_runs:
            anomalies.append("success_without_target_hold")

    # --- consistency checks -------------------------------------------------------------------------------------
    grasp_events = [ev for ev in target_events if ev["type"] == "grasp"]
    if grasp_events and grasped_f < 0:
        anomalies.append("grasp_event_without_progress_grasped_f")
    if grasped_f >= 0 and not target_runs and t is not None:
        anomalies.append("progress_grasped_f_without_debounced_hold")
    if grasp_events and reached_f >= 0 and reached_f > grasp_events[0]["first_after"]:
        anomalies.append("reached_after_first_grasp")
    if reached_f < 0 and grasp_events:
        anomalies.append("grasp_without_reached")
    seq = [stage_frames[k] for k in ("reached", "grasped", "lifted") if stage_frames[k] >= 0]
    if seq != sorted(seq):
        anomalies.append("stage_frames_non_monotone")
    if len(events) > 10:
        anomalies.append(f"many_events:{len(events)}")
    amb_frac = states.count("ambiguous") / max(n, 1)
    if amb_frac > 0.3:
        anomalies.append(f"ambiguous_frac:{amb_frac:.2f}")
    if not ep.success and meta.get("max_steps") and n < int(meta["max_steps"]):
        anomalies.append(f"failure_ended_early:{n}/{meta['max_steps']}")
    if t is not None and not valid[t]:
        anomalies.append("target_slot_invalid")

    return {
        "reference_version": REFERENCE_VERSION,
        "dataset": ep.name, "episode_index": int(ep.ep), "suite": meta.get("suite"), "task_id": meta.get("task_id"),
        "task": ep.task, "success": bool(ep.success),
        "n_frames": n, "fps": int(ep.fps), "n_chunks": len(chunks), "chunks": [[int(a), int(e)] for a, e in chunks],
        "object_slots": slots, "target_slot": slots[t] if t is not None else None, "goal_slot": goal_slot,
        "goal_region": goal_region, "fixtures": list(meta.get("fixtures", [])),
        "target_candidates": tg["movable"], "target_selection": tsel, "fixture_atoms": fixture_atoms,
        "held_runs": held_runs,
        "events": events,
        "wrong_object_contacts": wrong,
        "collisions": collisions,
        "fixture_motion": fixture_motion,
        "close_on_nothing": close_on_nothing,
        "attempts": attempts,
        "post_slip_closure": post_slip_closure,
        "stage_frames": stage_frames,
        "final": final,
        "failure_mode": mode, "mode_reason": reason, "cause": cause, "decisive_chunk": D,
        "chunk_labels": chunk_labels,
        "anomalies": anomalies,
        "frame_state_counts": dict(Counter(states)),
    }


# ----------------------------------------------------------------------------------------------- CLI
def ref_path(name, ep):
    return REF_DIR / name / f"episode_{int(ep):06d}.json"


def _open_with_retry(name, tries=3):
    last = None
    for k in range(tries):
        try:
            return open_dataset(name)
        except Exception as e:  # HF datasets cache races with other readers
            last = e
            time.sleep(2.0 * (k + 1))
    raise last


def summarize(names):
    """Read every reference on disk for the given datasets and print the tables."""
    refs = []
    for name in names:
        d = REF_DIR / name
        if d.exists():
            for p in sorted(d.glob("episode_*.json")):
                refs.append(json.loads(p.read_text()))
    fails = [r for r in refs if not r["success"]]
    succs = [r for r in refs if r["success"]]
    fam = lambda r: r["dataset"].split("__t")[0]  # noqa: E731
    families = sorted({fam(r) for r in refs})
    modes = list(MODES) + ["success"]
    print(f"\n== failure_mode counts ({len(fails)} failure references, {len(succs)} success references, {len(refs)} total)")
    w = max([len(f) for f in families] + [6])
    print(" " * w + " " + " ".join(f"{m[:11]:>11s}" for m in modes) + "   total")
    table = {f: Counter(r["failure_mode"] for r in refs if fam(r) == f) for f in families}
    for f in families:
        print(f"{f:{w}s} " + " ".join(f"{table[f].get(m, 0):11d}" for m in modes) + f" {sum(table[f].values()):7d}")
    tot = Counter(r["failure_mode"] for r in refs)
    print(f"{'ALL':{w}s} " + " ".join(f"{tot.get(m, 0):11d}" for m in modes) + f" {len(refs):7d}")
    if succs:
        print(f"\n== success references ({len(succs)})")
        rc = Counter(cl["rule"].split("+")[0] for r in succs for cl in r["chunk_labels"])
        ns = sum(rc.values())
        print("  chunk rules: " + ", ".join(f"{k}={v} ({v / ns:.1%})" for k, v in rc.most_common()))
        pc = Counter(cl["primary"] for r in succs for cl in r["chunk_labels"])
        print("  primary labels: " + ", ".join(f"{k}={v}" for k, v in pc.most_common()))
        print("  mode_reason: " + ", ".join(f"{k}={v}" for k, v in Counter(r["mode_reason"] for r in succs).most_common()))
        print("  cause: " + ", ".join(f"{k}={v}" for k, v in Counter(r["cause"] for r in succs).most_common()))
        print(f"  decisive set (recovered error): {sum(r['decisive_chunk'] is not None for r in succs)}/{len(succs)}")
        post = [sum(cl["rule"] == "post_success" for cl in r["chunk_labels"]) for r in succs]
        print(f"  post_success chunks per episode: mean {np.mean(post):.2f}, max {max(post)}, episodes with any: {sum(p > 0 for p in post)}")
        an = Counter(a.split(":")[0] for r in succs for a in r["anomalies"])
        print(f"  anomalies ({sum(bool(r['anomalies']) for r in succs)} episodes): " + ", ".join(f"{k}={v}" for k, v in an.most_common()))
        for r in [r for r in succs if r["anomalies"]][:10]:
            print(f"    {r['dataset']} ep{r['episode_index']:3d} {r['anomalies']}")
    if not fails:
        return refs
    modes = list(MODES)
    print("\n== sanity")
    fc = Counter()
    for r in fails:
        fc.update(r["frame_state_counts"])
    nf = sum(fc.values())
    print("  frame states: " + ", ".join(f"{k}={v / nf:.3f}" for k, v in sorted(fc.items())))
    eh = Counter(len(r["events"]) for r in fails)
    print("  events per episode: " + ", ".join(f"{k}:{eh[k]}" for k in sorted(eh)))
    th = Counter(len([e for e in r["events"] if e["type"] == t]) for r in fails for t in ("drop",))
    print("  drops per episode: " + ", ".join(f"{k}:{th[k]}" for k in sorted(th)))
    for m in modes:
        rs = [r for r in fails if r["failure_mode"] == m]
        if rs:
            nul = sum(r["decisive_chunk"] is None for r in rs)
            print(f"  decisive_chunk null rate {m:18s}: {nul}/{len(rs)}")
    rc = Counter(cl["rule"].split("+")[0] for r in fails for cl in r["chunk_labels"])
    print("  chunk rules: " + ", ".join(f"{k}={v}" for k, v in rc.most_common()))
    sc = sum(cl["scorable"] for r in fails for cl in r["chunk_labels"])
    print(f"  scorable chunks: {sc}/{sum(len(r['chunk_labels']) for r in fails)}")
    short = [ev for r in fails for ev in r["events"] if ev["type"] != "grasp" and ev.get("hold_frames", HOLD_MIN_FRAMES) < HOLD_MIN_FRAMES]
    print(f"  slips (holds < {HOLD_MIN_FRAMES} frames with events): {len(short)} in {len({(r['dataset'], r['episode_index']) for r in fails for ev in r['events'] if ev.get('hold_frames', HOLD_MIN_FRAMES) < HOLD_MIN_FRAMES})} episodes; "
          f"post_slip_closure runs: {sum(len(r.get('post_slip_closure', [])) for r in fails)} in {sum(bool(r.get('post_slip_closure')) for r in fails)} episodes")
    others = [r for r in fails if r["failure_mode"] == "other"]
    print(f"\n== 'other' episodes: {len(others)}")
    for k, v in Counter(r["mode_reason"].split(":")[0] for r in others).most_common():
        print(f"  {v:4d}  {k}")
    for r in others[:15]:
        print(f"  {r['dataset']} ep{r['episode_index']:3d} [{r['suite']} t{r['task_id']}] {r['mode_reason']}")
    an = Counter(a.split(":")[0] for r in fails for a in r["anomalies"])
    print(f"\n== anomalies ({sum(bool(r['anomalies']) for r in fails)} episodes)")
    for k, v in an.most_common():
        print(f"  {v:4d}  {k}")
    for r in [r for r in fails if r["anomalies"]][:15]:
        print(f"  {r['dataset']} ep{r['episode_index']:3d} {r['failure_mode']:16s} {r['anomalies']}")
    print("\n== target selection: " + ", ".join(f"{k}={v}" for k, v in Counter(r["target_selection"] for r in fails).most_common()))
    return refs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datasets", nargs="+", required=True, help="dataset names or family prefixes (full_shift8 ...)")
    ap.add_argument("--failures-only", action="store_true")
    ap.add_argument("--successes-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="max episodes to build per dataset")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--summary-only", action="store_true", help="only print the tables from references on disk")
    args = ap.parse_args()
    names = list_datasets(args.datasets)
    if args.summary_only:
        summarize(names)
        return
    print(f"datasets: {len(names)}  out: {REF_DIR}")
    built = skipped = failed = 0
    errors = []
    t0 = time.time()
    for name in names:
        rows = read_episodes_jsonl(name)
        if args.failures_only:
            rows = [r for r in rows if not r["success"]]
        if args.successes_only:
            rows = [r for r in rows if r["success"]]
        todo = [r for r in rows if args.overwrite or not ref_path(name, r["episode_index"]).exists()]
        if args.limit:
            todo = todo[: args.limit]
        skipped += len(rows) - len(todo)
        if not todo:
            continue
        try:
            ds = _open_with_retry(name)
        except Exception as e:
            errors.append((name, None, f"open: {str(e)[:120]}"))
            failed += len(todo)
            continue
        from common import Episode  # noqa: E402  (import after the heavy dataset import)

        modes = Counter()
        for r in todo:
            try:
                ref = build_reference(Episode(ds, name, r["episode_index"]))
                dump_json(ref, ref_path(name, r["episode_index"]))
                modes[ref["failure_mode"]] += 1
                built += 1
            except Exception as e:
                errors.append((name, r["episode_index"], f"{type(e).__name__}: {str(e)[:160]}"))
                failed += 1
        print(f"{name}: built {len(todo)} ({dict(modes)})  [{time.time() - t0:.0f}s]")
    print(f"\nbuilt {built}, skipped (existing) {skipped}, failed {failed}")
    for name, ep, msg in errors:
        print(f"  ERROR {name} ep{ep}: {msg}")
    summarize(names)


if __name__ == "__main__":
    main()
