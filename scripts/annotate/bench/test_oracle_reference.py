"""Unit tests for oracle_reference.py on synthetic Episode-like stubs (no datasets, CPU only).

Run: bench.sh test_oracle_reference.py   (or python -m unittest from scripts/annotate/bench)
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oracle_reference import (HOLD_GAP_FRAMES, HOLD_MIN_FRAMES, POST_SLIP_FRAMES, SLIP_COLLAPSE_FRAMES, build_reference, debounce,  # noqa: E402
                              drop_short_runs, expand_runs, hold_mask, is_slip, merge_gaps, rle)

K = 12  # slot capacity of the recorder arrays


class FakeEpisode:
    """Minimal stand-in for common.Episode: columns dict, 10-frame chunks, sidecar meta."""

    def __init__(self, n=300, slots=("target_1", "basket_1", "distractor_1"), goal="basket_1", success=False):
        self.n, self.fps, self.name, self.ep = n, 20, "fake__t0", 0
        self.slots = list(slots)
        self.meta = {"object_slots": self.slots, "target_objects": ["target_1", goal], "fixtures": [], "fixture_joint_names": [],
                     "goal_state": [["in", "target_1", f"{goal}_contain_region"]], "max_steps": n, "suite": "fake", "task_id": 0,
                     "task_language": "put the target in the basket", "success": success}
        z = lambda w: np.zeros((n, w), np.float32)  # noqa: E731
        c = {k: z(K) for k in ("priv.obj_gripper_contact", "priv.obj_left_finger_contact", "priv.obj_right_finger_contact", "priv.obj_grasped",
                                "priv.obj_support_contact", "priv.obj_obj_contact", "priv.obj_resting")}
        c["priv.target_mask"] = z(K); c["priv.target_mask"][:, [0, 1]] = 1
        c["priv.obj_valid"] = z(K); c["priv.obj_valid"][:, : len(self.slots)] = 1
        c["priv.obj_support_contact"][:, : len(self.slots)] = 1
        c["priv.obj_resting"][:, : len(self.slots)] = 1
        pos = np.zeros((n, K, 3), np.float32)
        pos[:, 0] = (0.5, 0.0, 0.9); pos[:, 1] = (0.5, 0.3, 0.9); pos[:, 2] = (0.3, -0.2, 0.9)
        c["priv.obj_pos"] = pos.reshape(n, -1)
        c["priv.eef_pos"] = np.tile(np.array([0.2, 0.0, 1.1], np.float32), (n, 1))
        for k in ("priv.arm_contacts", "priv.gripper_static_contacts", "priv.gripper_fixture_contacts", "next.success"):
            c[k] = z(1)
        c["priv.fixture_qpos"], c["priv.fixture_valid"] = z(16), z(16)
        c["observation.state"] = z(8); c["observation.state"][:, 6] = 0.04
        c["action"] = z(7); c["action"][:, 6] = -1.0
        ci = np.repeat(np.arange((n + 9) // 10), 10)[:n].reshape(n, 1)
        c["chunk.index"] = ci.astype(np.int64)
        self.cols = c
        self.move(0, 50, (0.2, 0.0, 1.1), (0.5, 0.0, 0.93))  # default: approach the target over the first 50 frames

    # --- interface used by build_reference -----------------------------------------------------------------------
    def col(self, k):
        return self.cols[k]

    @property
    def chunks(self):
        return [(i, min(self.n, i + 10)) for i in range(0, self.n, 10)]

    @property
    def n_chunks(self):
        return len(self.chunks)

    def chunk_of_frame(self, i):
        return min(int(i) // 10, self.n_chunks - 1)

    @property
    def success(self):
        return self.meta["success"]

    @property
    def task(self):
        return self.meta["task_language"]

    @property
    def gripper_aperture(self):
        return self.cols["observation.state"][:, 6].astype(np.float64)

    @property
    def gripper_cmd(self):
        return self.cols["action"][:, 6].astype(np.float64)

    # --- scenario helpers -----------------------------------------------------------------------------------------
    def move(self, a, b, p0, p1):
        """Linear eef motion from frame a to b (inclusive), then hold p1 until the end."""
        p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
        eef = self.cols["priv.eef_pos"]
        for i in range(a, b + 1):
            eef[i] = p0 + (p1 - p0) * (i - a) / max(b - a, 1)
        eef[b + 1:] = p1

    def contact(self, slot, a, b, fingers="both"):
        s = self.slots.index(slot)
        self.cols["priv.obj_gripper_contact"][a:b + 1, s] = 1
        if fingers in ("both", "left"):
            self.cols["priv.obj_left_finger_contact"][a:b + 1, s] = 1
        if fingers in ("both", "right"):
            self.cols["priv.obj_right_finger_contact"][a:b + 1, s] = 1

    def grasp(self, slot, a, b, lift_from=None, cmd_close_until=None, aperture=0.02):
        """Grasped flag on [a, b]; object airborne and following the eef from lift_from; CLOSE command a-3..cmd_close_until."""
        s = self.slots.index(slot)
        self.contact(slot, a, b)
        self.cols["priv.obj_grasped"][a:b + 1, s] = 1
        self.cols["action"][max(a - 3, 0):(cmd_close_until if cmd_close_until is not None else b) + 1, 6] = 1.0
        self.cols["observation.state"][a:, 6] = aperture
        if lift_from is not None:
            self.cols["priv.obj_support_contact"][lift_from:b + 1, s] = 0
            self.cols["priv.obj_resting"][lift_from:b + 1, s] = 0
            pos = self.cols["priv.obj_pos"].reshape(self.n, K, 3)
            pos[lift_from:b + 1, s] = self.cols["priv.eef_pos"][lift_from:b + 1] - (0, 0, 0.03)
            pos[b + 1:, s] = pos[b, s] - (0, 0, 0.05)  # lands below where it was let go
        return self

    def release(self, b):
        """Open command from frame b-1 on (the hold must end at b)."""
        self.cols["action"][b - 1:, 6] = -1.0
        self.cols["observation.state"][b + 2:, 6] = 0.04
        return self


def states_of(ref):
    return expand_runs(ref["held_runs"], ref["n_frames"])[0]


def rule_of(ref, c):
    return ref["chunk_labels"][c]["rule"], set(ref["chunk_labels"][c]["allowed"])


class PrimitiveTests(unittest.TestCase):
    def test_debounce_hysteresis(self):
        raw = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1], bool)
        out = debounce(raw, 3)
        exp = np.array([0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1], bool)
        np.testing.assert_array_equal(out, exp)  # 2-frame blip dropped, 1-frame gap filled, tail run kept
        self.assertFalse(debounce(np.array([1, 1, 0, 1, 1, 0], bool), 3).any())

    def test_merge_gaps_and_min_hold(self):
        self.assertEqual((HOLD_GAP_FRAMES, HOLD_MIN_FRAMES), (4, 8))
        raw = np.zeros(40, bool)
        raw[5:15] = True; raw[19:30] = True  # gap 15..18 = 4 frames -> merged
        raw[35:38] = True  # 3-frame run: passes debounce, not the min hold length
        m = merge_gaps(raw, 4)
        self.assertTrue(m[5:30].all()); self.assertFalse(m[:5].any()); self.assertFalse(m[30:35].any())
        self.assertFalse(merge_gaps(raw, 3)[15:19].any())  # a 4-frame gap is not merged with gap=3
        d = drop_short_runs(m, 8)
        self.assertTrue(d[5:30].all()); self.assertFalse(d[35:38].any())
        self.assertFalse(drop_short_runs(np.ones(7, bool), 8).any()); self.assertTrue(drop_short_runs(np.ones(8, bool), 8).all())
        h = hold_mask(raw)
        self.assertTrue(h[5:30].all()); self.assertFalse(h[30:].any())
        seen = []
        h2 = hold_mask(raw, keep_short=lambda a, e: seen.append((a, e)) or a == 35)  # r3: a short run kept when the callback says slip
        self.assertEqual(seen, [(35, 39)])  # the debounce hysteresis keeps the tail (2 trailing False frames) inside the run
        self.assertTrue(h2[35:40].all()); self.assertTrue(h2[5:30].all()); self.assertFalse(h2[30:35].any())

    def test_is_slip(self):
        n = 40
        cmd, grip = np.ones(n), np.full(n, 0.02)
        air = np.zeros(n, bool)
        self.assertEqual((POST_SLIP_FRAMES, SLIP_COLLAPSE_FRAMES), (12, 10))
        self.assertFalse(is_slip(10, 16, air, cmd, grip))  # closed command, no lift, no collapse: a finger push
        air2 = air.copy(); air2[15] = True
        self.assertTrue(is_slip(10, 16, air2, cmd, grip))  # airborne at one frame of the hold
        grip2 = grip.copy(); grip2[26] = 0.001  # collapse 10 frames after the hold ends (frames 17..26 are the window)
        self.assertTrue(is_slip(10, 16, air, cmd, grip2))
        grip3 = grip.copy(); grip3[27] = 0.001  # one frame too late
        self.assertFalse(is_slip(10, 16, air, cmd, grip3))
        cmd2 = cmd.copy(); cmd2[17] = -1.0  # the command opens at the transition: a release, not a slip
        self.assertFalse(is_slip(10, 16, air, cmd2, grip2))
        self.assertFalse(is_slip(30, 39, air, cmd, grip2))  # hold reaches the end: no collapse window (airborne test only)

    def test_rle_round_trip(self):
        rng = np.random.default_rng(0)
        for _ in range(20):
            n = int(rng.integers(1, 60))
            st = rng.choice(["held", "empty", "ambiguous"], size=n).tolist()
            ob = [None if s == "empty" else "o" for s in st]
            runs = rle(st, ob)
            self.assertEqual(runs[0]["start"], 0)
            self.assertEqual(runs[-1]["end"], n - 1)
            self.assertTrue(all(runs[i]["end"] + 1 == runs[i + 1]["start"] for i in range(len(runs) - 1)))
            s2, o2 = expand_runs(runs, n)
            self.assertEqual((s2, o2), (st, ob))


class HeldStateTests(unittest.TestCase):
    def test_short_grasp_blip_is_ambiguous_not_held(self):
        ep = FakeEpisode()
        ep.contact("target_1", 50, 60)
        ep.cols["priv.obj_grasped"][52:54, 0] = 1  # 2 frames < DEBOUNCE
        ref = build_reference(ep)
        st = states_of(ref)
        self.assertEqual(st[52], "ambiguous"); self.assertEqual(st[53], "ambiguous")
        self.assertEqual(st[55], "empty")
        self.assertEqual(ref["events"], [])
        self.assertEqual(ref["failure_mode"], "missed_grasp")

    def test_gap_inside_hold_is_filled_and_ambiguous(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 100, lift_from=60, cmd_close_until=110)
        ep.cols["priv.obj_grasped"][70, 0] = 0
        ref = build_reference(ep)
        st, ob = expand_runs(ref["held_runs"], ep.n)
        self.assertEqual(st[70], "ambiguous"); self.assertEqual(ob[70], "target_1")
        self.assertEqual(st[69], "held"); self.assertEqual(st[71], "held")
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp", "drop"])  # one hold, not two

    def test_transition_and_xor_frames(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 100, lift_from=60)
        ep.contact("distractor_1", 20, 20, fingers="left")  # exactly one finger
        ref = build_reference(ep)
        st, ob = expand_runs(ref["held_runs"], ep.n)
        for i in (48, 49, 50, 51, 99, 100, 101, 102):
            self.assertEqual(st[i], "ambiguous", i)
        for i in (47, 103):
            self.assertEqual(st[i], "empty", i)
        self.assertEqual(st[52], "held"); self.assertEqual(st[98], "held"); self.assertEqual(ob[52], "target_1")
        self.assertEqual(st[20], "ambiguous"); self.assertEqual(ob[20], "distractor_1")
        self.assertEqual(st[19], "empty")
        self.assertEqual(ref["held_runs"][0], {"start": 0, "end": 19, "state": "empty", "object": None})

    def test_short_lifted_hold_is_a_slip_with_events(self):
        # r3 (full_shift8__t1 ep 3 frames 150-156): 7 frames of grasp flag, the object leaves the table, contact lost with
        # the command still CLOSE -> a real hold with grasp + drop events; r2 demoted it to ambiguous with no event
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 56, lift_from=52, cmd_close_until=60)
        ref = build_reference(ep)
        self.assertEqual([(e["type"], e["chunk"], e["hold_frames"]) for e in ref["events"]], [("grasp", 4, 7), ("drop", 5, 7)])
        self.assertEqual((ref["events"][1]["last_before"], ref["events"][1]["first_after"]), (56, 57))
        st, ob = expand_runs(ref["held_runs"], ep.n)
        self.assertEqual((st[53], ob[53]), ("held", "target_1"))
        self.assertEqual(st[49], "ambiguous")  # transition frame of a real hold now
        self.assertEqual(st[47], "empty"); self.assertEqual(st[59], "empty")
        self.assertEqual(ref["failure_mode"], "drop_transport"); self.assertEqual(ref["decisive_chunk"], 5)
        self.assertEqual(rule_of(ref, 5), ("decisive", {"failure_inducing"}))
        ep2 = FakeEpisode()
        ep2.grasp("target_1", 50, 57, lift_from=52, cmd_close_until=60)  # 8 frames: a hold as before
        ref2 = build_reference(ep2)
        self.assertEqual([e["type"] for e in ref2["events"]], ["grasp", "drop"])
        self.assertEqual(ref2["events"][1]["hold_frames"], 8)
        self.assertEqual(ref2["failure_mode"], "drop_transport")

    def test_short_hold_ending_in_collapse_is_a_slip(self):
        # never lifted, 7 frames, command stays CLOSE and the aperture collapses 3 frames after the contact is lost
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 56, cmd_close_until=70)
        ep.cols["observation.state"][59:70, 6] = 0.001
        ref = build_reference(ep)
        self.assertEqual([(e["type"], e["chunk"]) for e in ref["events"]], [("grasp", 4), ("drop", 5)])
        self.assertEqual(states_of(ref)[53], "held")
        self.assertEqual(ref["failure_mode"], "missed_grasp"); self.assertIn("slip_drop", ref["mode_reason"])
        self.assertEqual(ref["decisive_chunk"], 5)  # the slip's chunk, not the closure's
        # the closure that follows is the same failed attempt: recorded as post_slip_closure, not a close-on-nothing error
        self.assertEqual(ref["close_on_nothing"], [])
        self.assertEqual([(p["start"], p["end"], p["chunk"], p["after_drop"]) for p in ref["post_slip_closure"]], [(59, 69, 5, 56)])
        self.assertEqual(rule_of(ref, 5), ("decisive", {"failure_inducing"}))
        self.assertNotIn("failure_inducing", rule_of(ref, 6)[1])
        ep2 = FakeEpisode()
        ep2.grasp("target_1", 50, 56, cmd_close_until=70)
        ep2.cols["observation.state"][66:70, 6] = 0.001  # collapse exactly SLIP_COLLAPSE_FRAMES after the hold (frame 66)
        self.assertEqual([e["type"] for e in build_reference(ep2)["events"]], ["grasp", "drop"])
        ep3 = FakeEpisode()
        ep3.grasp("target_1", 50, 56, cmd_close_until=70)
        ep3.cols["observation.state"][68:70, 6] = 0.001  # 11 frames after: too late, the short hold stays ambiguous
        self.assertEqual(build_reference(ep3)["events"], [])

    def test_short_brush_stays_ambiguous_without_event(self):
        ep = FakeEpisode()
        ep.contact("target_1", 50, 56)
        ep.cols["priv.obj_grasped"][50:57, 0] = 1  # both pads on the object for 7 frames, command OPEN throughout, no lift
        ref = build_reference(ep)
        st, ob = expand_runs(ref["held_runs"], ep.n)
        self.assertTrue(all(st[i] == "ambiguous" for i in range(50, 57)), st[48:60])
        self.assertEqual(ob[53], "target_1")
        self.assertEqual(st[49], "empty"); self.assertEqual(st[57], "empty")
        self.assertNotIn("held", [r["state"] for r in ref["held_runs"]])
        self.assertEqual(ref["events"], []); self.assertEqual(ref["post_slip_closure"], [])
        self.assertEqual(ref["failure_mode"], "missed_grasp"); self.assertIsNone(ref["decisive_chunk"])
        self.assertTrue(all(cl["rule"] == "unlocalised_missed_grasp" and not cl["scorable"] for cl in ref["chunk_labels"]))  # no event to label from
        ep2 = FakeEpisode()
        ep2.grasp("target_1", 50, 56, cmd_close_until=70)  # closed command but no lift and no collapse: a finger push
        ref2 = build_reference(ep2)
        self.assertEqual(ref2["events"], [])
        self.assertEqual(states_of(ref2)[53], "ambiguous")

    def test_post_slip_closure_window(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 56, lift_from=52, cmd_close_until=90)
        ep.cols["observation.state"][70:80, 6] = 0.001  # closure 14 frames after the drop: a new attempt, an error of its own
        ref = build_reference(ep)
        self.assertEqual(ref["post_slip_closure"], [])
        self.assertEqual(ref["close_on_nothing"][0]["start"], 70)
        self.assertEqual(ref["failure_mode"], "drop_transport"); self.assertEqual(ref["decisive_chunk"], 5)
        self.assertEqual(rule_of(ref, 7), ("post_event", {"failure_inducing", "aftermath", "recovery"}))
        ep2 = FakeEpisode()
        ep2.grasp("target_1", 50, 60, lift_from=52, cmd_close_until=70)  # an 11-frame hold: the suppression is not only for short holds
        ep2.cols["observation.state"][63:70, 6] = 0.001
        ref2 = build_reference(ep2)
        self.assertEqual(ref2["close_on_nothing"], [])
        self.assertEqual([(p["start"], p["after_drop"]) for p in ref2["post_slip_closure"]], [(63, 60)])
        self.assertEqual(ref2["decisive_chunk"], 6)

    def test_holds_separated_by_short_gap_are_merged(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 70, lift_from=60, cmd_close_until=100)
        ep.grasp("target_1", 75, 100, lift_from=80, cmd_close_until=110)  # 4-frame flag gap 71..74
        ref = build_reference(ep)
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp", "drop"])
        self.assertEqual(ref["events"][1]["hold_frames"], 51)
        st, ob = expand_runs(ref["held_runs"], ep.n)
        for i in range(71, 75):
            self.assertEqual((st[i], ob[i]), ("ambiguous", "target_1"), i)
        self.assertEqual(st[70], "held"); self.assertEqual(st[75], "held")
        self.assertEqual(ref["failure_mode"], "drop_transport"); self.assertEqual(ref["decisive_chunk"], 10)
        ep2 = FakeEpisode()
        ep2.grasp("target_1", 50, 70, lift_from=60, cmd_close_until=100)
        ep2.grasp("target_1", 76, 100, lift_from=80, cmd_close_until=110)  # 5-frame gap: two holds
        ref2 = build_reference(ep2)
        self.assertEqual([e["type"] for e in ref2["events"]], ["grasp", "drop", "grasp", "drop"])
        self.assertEqual(expand_runs(ref2["held_runs"], ep2.n)[0][73], "empty")


class EventTests(unittest.TestCase):
    def test_drop_when_command_still_close(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 100, lift_from=60, cmd_close_until=110)
        ref = build_reference(ep)
        ev = ref["events"]
        self.assertEqual([e["type"] for e in ev], ["grasp", "drop"])
        self.assertEqual((ev[0]["last_before"], ev[0]["first_after"], ev[0]["chunk"]), (49, 50, 4))
        self.assertEqual((ev[1]["last_before"], ev[1]["first_after"], ev[1]["chunk"]), (100, 101, 10))
        self.assertFalse(ev[1]["gripper_cmd_open"])
        self.assertEqual(ref["failure_mode"], "drop_transport"); self.assertEqual(ref["cause"], "grasp")
        self.assertEqual(ref["decisive_chunk"], 10)

    def test_release_when_command_opens(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 100, lift_from=60).release(100)
        ref = build_reference(ep)
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp", "release"])
        self.assertTrue(ref["events"][1]["gripper_cmd_open"])
        self.assertEqual(ref["failure_mode"], "release_miss"); self.assertEqual(ref["cause"], "manipulation")
        self.assertEqual(ref["decisive_chunk"], 10)

    def test_decisive_boundary_admits_failure_inducing_in_next_chunk(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 99, lift_from=60, cmd_close_until=110)  # last_before 99 (chunk 9), first_after 100 (chunk 10)
        ref = build_reference(ep)
        self.assertEqual(ref["decisive_chunk"], 9)
        rule, allowed = rule_of(ref, 10)
        self.assertIn("decisive_boundary", rule); self.assertIn("failure_inducing", allowed)


class FailureModeTests(unittest.TestCase):
    def test_never_reached(self):
        ep = FakeEpisode()
        ep.move(0, 50, (0.2, 0.0, 1.1), (0.3, 0.1, 1.0))
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "never_reached"); self.assertEqual(ref["cause"], "reaching")
        self.assertIsNone(ref["decisive_chunk"])
        self.assertTrue(all(cl["rule"] == "unlocalised" and not cl["scorable"] for cl in ref["chunk_labels"]))
        self.assertEqual(set(ref["chunk_labels"][0]["allowed"]), {"failure_inducing", "neutral", "progress"})

    def test_wrong_object(self):
        ep = FakeEpisode()
        ep.grasp("distractor_1", 33, 60, lift_from=40, cmd_close_until=110)
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "wrong_object"); self.assertEqual(ref["cause"], "sequencing_semantic")
        self.assertEqual(ref["decisive_chunk"], 3)
        self.assertEqual(ref["wrong_object_contacts"][0]["object"], "distractor_1")
        rule, allowed = rule_of(ref, 1)
        self.assertIn("wrong_approach", rule); self.assertIn("failure_inducing", allowed)

    def test_brief_wrong_brush_does_not_decide_the_mode(self):
        ep = FakeEpisode()
        ep.contact("distractor_1", 30, 34)  # 5-frame brush, no grasp
        ep.contact("target_1", 60, 65)
        ep.cols["action"][64:90, 6] = 1.0; ep.cols["observation.state"][68:90, 6] = 0.001
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "missed_grasp")
        self.assertEqual(rule_of(ref, 3), ("wrong_contact_brush", {"failure_inducing", "progress", "neutral"}))
        ep2 = FakeEpisode()
        ep2.contact("distractor_1", 30, 45)  # 16 frames, target never touched
        self.assertEqual(build_reference(ep2)["failure_mode"], "wrong_object")
        ep3 = FakeEpisode()
        ep3.contact("distractor_1", 30, 34)  # brush only, target never touched
        ref3 = build_reference(ep3)
        self.assertEqual(ref3["failure_mode"], "never_reached"); self.assertIn("brushed", ref3["mode_reason"])

    def test_missed_grasp_decisive_is_first_close_on_nothing_after_contact(self):
        ep = FakeEpisode()
        ep.contact("target_1", 40, 45)
        ep.cols["action"][44:80, 6] = 1.0
        ep.cols["observation.state"][48:80, 6] = 0.001  # closed on nothing from frame 48
        ep.cols["action"][10:14, 6] = 1.0; ep.cols["observation.state"][12:14, 6] = 0.0  # early close before contact: not decisive
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "missed_grasp"); self.assertEqual(ref["cause"], "grasp")
        self.assertEqual(ref["decisive_chunk"], 4)
        self.assertEqual(ref["close_on_nothing"][0]["start"], 12)
        self.assertEqual(rule_of(ref, 1), ("other_event", {"failure_inducing"}))
        self.assertEqual(ref["stage_frames"]["reached"], 40); self.assertEqual(ref["stage_frames"]["grasped"], -1)

    def test_hold_no_release_near_goal(self):
        ep = FakeEpisode()
        ep.move(50, 150, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))  # carry to the basket, then freeze
        ep.grasp("target_1", 50, ep.n - 1, lift_from=60)
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "hold_no_release"); self.assertEqual(ref["cause"], "manipulation")
        self.assertEqual(ref["decisive_chunk"], 15)
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp"])
        self.assertGreaterEqual(ref["stage_frames"]["transported"], 0)
        self.assertEqual(rule_of(ref, 12), ("advance_transporting", {"progress"}))
        self.assertEqual(rule_of(ref, 20), ("post_held_unscorable", {"progress", "recovery", "neutral", "aftermath"}))

    def test_stall_after_grasp_far_from_goal(self):
        ep = FakeEpisode()
        ep.move(50, 100, (0.5, 0.0, 0.93), (0.5, 0.05, 1.05))  # lift a little, then freeze far from the basket
        ep.grasp("target_1", 50, ep.n - 1, lift_from=60)
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "stall_after_grasp")
        self.assertEqual(ref["decisive_chunk"], 10)
        self.assertEqual(rule_of(ref, 20), ("post_held_unscorable", {"progress", "recovery", "neutral", "aftermath"}))
        self.assertTrue(ref["chunk_labels"][20]["scorable"])

    def test_hold_ending_within_debounce_of_the_end_is_held_at_end(self):
        ep = FakeEpisode()
        ep.move(50, 150, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
        ep.grasp("target_1", 50, ep.n - 4, lift_from=60)  # grasped flag off for the last 3 frames
        ref = build_reference(ep)
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp"])  # no drop/release for the tail
        self.assertEqual(ref["failure_mode"], "hold_no_release"); self.assertEqual(ref["decisive_chunk"], 15)
        self.assertIn("held_at_end_idle150_near_goal", ref["mode_reason"])
        ep2 = FakeEpisode()
        ep2.move(50, 150, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
        ep2.grasp("target_1", 50, ep2.n - 5, lift_from=60)  # off for the last 4 frames: a real end of hold
        ref2 = build_reference(ep2)
        self.assertEqual([e["type"] for e in ref2["events"]], ["grasp", "release"])
        self.assertEqual(ref2["failure_mode"], "release_miss"); self.assertEqual(ref2["decisive_chunk"], 29)

    def test_late_hold_at_timeout_is_hold_no_release_not_a_late_attempt(self):
        ep = FakeEpisode()
        ep.move(280, ep.n - 1, (0.5, 0.0, 0.93), (0.5, 0.1, 1.0))  # still moving at the end (set before grasp so the object follows)
        ep.grasp("target_1", 50, 100, lift_from=60, cmd_close_until=110)
        ep.grasp("target_1", 270, ep.n - 1, lift_from=280)  # re-grasped 30 frames before timeout
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "hold_no_release"); self.assertEqual(ref["cause"], "manipulation")
        self.assertIsNone(ref["decisive_chunk"])
        self.assertEqual(ref["mode_reason"], "active_hold30_no_idle_after_drop")
        self.assertEqual([(e["type"], e["chunk"]) for e in ref["events"]], [("grasp", 4), ("drop", 10), ("grasp", 26)])
        # r3: decisive stays null, but the chunk labels come from the events (r2: every chunk unlocalised, unscorable)
        self.assertTrue(all(cl["scorable"] for cl in ref["chunk_labels"]))
        self.assertFalse(any(cl["rule"].startswith("unlocalised") for cl in ref["chunk_labels"]))
        self.assertEqual(rule_of(ref, 10), ("other_event", {"failure_inducing"}))
        self.assertEqual(rule_of(ref, 12), ("idle", {"neutral"}))
        self.assertEqual(rule_of(ref, 26), ("regrasp", {"recovery"}))
        self.assertEqual(rule_of(ref, 28)[1], {"progress"}); self.assertTrue(rule_of(ref, 28)[0].startswith("advance_lifting"))  # still carrying at timeout
        self.assertEqual([cl["chunk"] for cl in ref["chunk_labels"] if cl["primary"] == "failure_inducing"], [10])
        ep2 = FakeEpisode()
        ep2.move(280, ep2.n - 1, (0.5, 0.0, 0.93), (0.5, -0.1, 0.93))  # moving away from the basket, level: no advance, not idle
        ep2.grasp("target_1", 270, ep2.n - 1, lift_from=271)
        ref2 = build_reference(ep2)
        self.assertEqual(ref2["failure_mode"], "hold_no_release"); self.assertEqual(ref2["mode_reason"], "active_hold30_no_idle")
        self.assertIsNone(ref2["decisive_chunk"])
        self.assertEqual(rule_of(ref2, 27)[1], {"progress"}); self.assertTrue(rule_of(ref2, 27)[0].startswith("advance"))  # contact/grasp/lift onsets
        for c in (28, 29):
            self.assertEqual(rule_of(ref2, c), ("final_hold_active", {"progress", "neutral"}), c)
            self.assertEqual(ref2["chunk_labels"][c]["primary"], "progress")
        self.assertEqual(rule_of(ref2, 3), ("advance_approach", {"progress"}))
        self.assertEqual(rule_of(ref2, 10), ("idle", {"neutral"}))
        self.assertFalse(any("failure_inducing" in cl["allowed"] for cl in ref2["chunk_labels"]))  # no error happened

    def test_collision_precedes_other_error(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 100, lift_from=60, cmd_close_until=110)
        ep.cols["priv.arm_contacts"][20:36, 0] = 1  # 16 frames
        ep.cols["priv.arm_contacts"][5:8, 0] = 1  # 3 frames: listed, but too short for the mode
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "collision"); self.assertEqual(ref["cause"], "collision")
        self.assertEqual(ref["decisive_chunk"], 2)
        self.assertEqual(len(ref["collisions"]), 2)
        self.assertIn("drop_transport", ref["mode_reason"])
        rule, allowed = rule_of(ref, 12)
        self.assertIn("post_collision", rule); self.assertIn("progress", allowed)

    def test_collision_after_error_does_not_override(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 100, lift_from=60, cmd_close_until=110)
        ep.cols["priv.arm_contacts"][150:200, 0] = 1
        self.assertEqual(build_reference(ep)["failure_mode"], "drop_transport")

    def test_hold_without_lift_is_a_failed_grasp(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 60, cmd_close_until=70)  # closed on the object, never lifted, slipped
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "missed_grasp"); self.assertEqual(ref["cause"], "grasp")
        self.assertEqual(ref["decisive_chunk"], 6)
        self.assertIn("slip_drop", ref["mode_reason"])
        self.assertEqual(rule_of(ref, 6), ("decisive", {"failure_inducing"}))
        ep2 = FakeEpisode()
        ep2.grasp("target_1", 50, 60).release(60)  # closed, then opened again without lifting
        ep2.grasp("target_1", 120, 130, cmd_close_until=140)
        ref2 = build_reference(ep2)
        self.assertEqual(ref2["failure_mode"], "missed_grasp")
        self.assertEqual(ref2["decisive_chunk"], 6)  # first failed closure
        self.assertEqual(rule_of(ref2, 13), ("failed_acquisition", {"failure_inducing"}))  # later failed acquisition, after D

    def test_long_active_hold_is_hold_no_release_with_event_labels(self):
        ep = FakeEpisode()
        eef = ep.cols["priv.eef_pos"]
        for i in range(60, ep.n):  # carry to the basket and keep jittering 4 mm/frame until timeout
            eef[i] = (0.5, min(0.3, 0.004 * (i - 60)), 1.0 + (0.004 if i % 2 else 0.0))
        ep.grasp("target_1", 50, ep.n - 1, lift_from=60)  # after the motion, so the object follows the eef
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "hold_no_release")
        self.assertIsNone(ref["decisive_chunk"])
        self.assertIn("active_hold250_no_idle", ref["mode_reason"])
        # r3: decisive null, labels from the events; r2 made every chunk unlocalised (q = 0 in the training export)
        self.assertTrue(all(cl["scorable"] for cl in ref["chunk_labels"]))
        self.assertEqual(rule_of(ref, 8), ("advance_transporting", {"progress"}))
        for c in (20, 29):
            self.assertEqual(rule_of(ref, c), ("final_hold_active", {"progress", "neutral"}), c)
            self.assertEqual(ref["chunk_labels"][c]["primary"], "progress")
        self.assertFalse(any("failure_inducing" in cl["allowed"] for cl in ref["chunk_labels"]))
        rules = {cl["rule"].split("+")[0] for cl in ref["chunk_labels"]}
        self.assertFalse(rules & {"unlocalised", "unlocalised_hold_no_release", "post_held_unscorable"})

    def test_never_reached_and_eventless_episodes_stay_unlocalised(self):
        ep = FakeEpisode()
        ep.move(0, 50, (0.2, 0.0, 1.1), (0.3, 0.1, 1.0))
        ref = build_reference(ep)
        self.assertEqual((ref["failure_mode"], ref["decisive_chunk"]), ("never_reached", None))
        self.assertTrue(all(cl["rule"] == "unlocalised" and not cl["scorable"] and set(cl["allowed"]) == {"failure_inducing", "neutral", "progress"}
                            for cl in ref["chunk_labels"]))
        ep2 = FakeEpisode()
        ep2.contact("target_1", 40, 45)  # touched the target, never closed the gripper: no event to label from
        ref2 = build_reference(ep2)
        self.assertEqual((ref2["failure_mode"], ref2["decisive_chunk"], ref2["events"]), ("missed_grasp", None, []))
        self.assertTrue(all(cl["rule"] == "unlocalised_missed_grasp" and not cl["scorable"] for cl in ref2["chunk_labels"]))


class ChunkLabelTests(unittest.TestCase):
    def test_post_decisive_held_chunks_are_post_held_unscorable(self):
        ep = FakeEpisode()
        ep.grasp("distractor_1", 33, 60, lift_from=40, cmd_close_until=110)  # wrong object first
        ep.grasp("target_1", 120, 200, lift_from=130, cmd_close_until=210)  # then a long carry of the target, dropped
        ref = build_reference(ep)
        self.assertEqual(ref["failure_mode"], "wrong_object"); self.assertEqual(ref["decisive_chunk"], 3)
        self.assertEqual(rule_of(ref, 11), ("regrasp", {"recovery"}))  # grasp event, last_before 119
        for c in range(12, 20):
            self.assertEqual(rule_of(ref, c), ("post_held_unscorable", {"progress", "recovery", "neutral", "aftermath"}), c)
            self.assertTrue(ref["chunk_labels"][c]["scorable"])
        self.assertEqual(rule_of(ref, 20), ("post_event", {"failure_inducing", "aftermath", "recovery"}))  # the drop, last_before 200
        self.assertEqual(rule_of(ref, 21), ("post_recoverable", {"neutral", "aftermath", "recovery"}))
        self.assertEqual(rule_of(ref, 27), ("post_other", {"aftermath", "neutral"}))

    def test_pre_decisive_sets(self):
        ep = FakeEpisode()
        ep.move(0, 30, (0.2, 0.0, 1.1), (0.5, 0.0, 0.93))  # approach done by frame 30, idle 30..49
        ep.grasp("target_1", 50, 120, lift_from=60, cmd_close_until=130)
        ep.move(60, 70, (0.5, 0.0, 0.93), (0.5, 0.0, 1.0))  # lift
        ref = build_reference(ep)
        self.assertEqual(ref["decisive_chunk"], 12)
        self.assertEqual(rule_of(ref, 0)[1], {"progress"}); self.assertTrue(rule_of(ref, 0)[0].startswith("advance"))
        self.assertEqual(rule_of(ref, 3), ("idle", {"neutral"}))
        self.assertEqual(rule_of(ref, 4)[1], {"progress"})  # grasp onset (frame 50 = first frame of chunk 5, caused by chunk 4)
        self.assertEqual(rule_of(ref, 6)[1], {"progress"})  # lifting
        self.assertEqual(rule_of(ref, 9), ("idle", {"neutral"}))  # holding still in the air, gripper steady
        ep.cols["priv.eef_pos"][95] += (0.0, 0.004, 0.0)  # a single 4 mm twitch: no longer idle, no stage change
        self.assertEqual(rule_of(build_reference(ep), 9), ("pre_other", {"progress", "neutral"}))
        self.assertEqual(rule_of(ref, 12), ("decisive", {"failure_inducing"}))
        self.assertEqual(rule_of(ref, 29), ("post_other", {"aftermath", "neutral"}))  # < 40 frames remaining

    def test_regrasp_is_recovery_and_earlier_drop_is_failure_inducing(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 80, lift_from=60, cmd_close_until=85)
        ep.grasp("target_1", 120, 160, lift_from=130).release(160)
        ep.cols["observation.state"][85:120, 6] = 0.04
        ref = build_reference(ep)
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp", "drop", "grasp", "release"])
        self.assertEqual(ref["failure_mode"], "release_miss"); self.assertEqual(ref["decisive_chunk"], 16)
        self.assertEqual(rule_of(ref, 8), ("other_event", {"failure_inducing"}))
        self.assertEqual(rule_of(ref, 11), ("regrasp", {"recovery"}))
        self.assertEqual(rule_of(ref, 10), ("idle", {"neutral"}))
        self.assertEqual(rule_of(ref, 16), ("decisive", {"failure_inducing"}))
        self.assertEqual(rule_of(ref, 17)[1], {"neutral", "aftermath", "recovery"})

    def test_every_chunk_has_allowed_primary_rule(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 100, lift_from=60, cmd_close_until=110)
        ref = build_reference(ep)
        self.assertEqual(len(ref["chunk_labels"]), ep.n_chunks)
        self.assertEqual(ref["reference_version"], "r6")
        for cl in ref["chunk_labels"]:
            self.assertIn(cl["primary"], cl["allowed"])
            self.assertTrue(cl["rule"])
        self.assertEqual(len(ref["events"]), 2)
        for ev in ref["events"]:
            self.assertEqual(ev["chunk"], ep.chunk_of_frame(ev["last_before"]))  # event chunk = chunk of last_before
        for key in ("held_runs", "events", "wrong_object_contacts", "collisions", "fixture_motion", "stage_frames", "final",
                    "failure_mode", "cause", "decisive_chunk", "chunk_labels", "chunks", "target_slot", "goal_slot", "reference_version"):
            self.assertIn(key, ref)


class SuccessTests(unittest.TestCase):
    """Success references (training labels): the pre-decisive rules with the outcome known, plus post_success."""

    @staticmethod
    def clean(n=200):
        ep = FakeEpisode(n=n, success=True)
        ep.move(50, 150, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))  # carry to the basket
        ep.grasp("target_1", 50, 160, lift_from=60).release(160)
        ep.cols["next.success"][150:, 0] = 1  # the action of frame 150 satisfies the predicate
        return ep

    def test_clean_success(self):
        ref = build_reference(self.clean())
        self.assertEqual((ref["failure_mode"], ref["cause"], ref["decisive_chunk"], ref["mode_reason"]), ("success", "unclear", None, "success"))
        self.assertTrue(ref["success"])
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp", "release"])
        self.assertEqual(ref["stage_frames"]["placed"], 150)
        self.assertEqual(rule_of(ref, 0)[1], {"progress"}); self.assertTrue(rule_of(ref, 0)[0].startswith("advance"))
        self.assertEqual(rule_of(ref, 4)[1], {"progress"})  # grasp onset
        self.assertEqual(rule_of(ref, 12), ("advance_transporting", {"progress"}))
        self.assertEqual(rule_of(ref, 15), ("advance_placed", {"progress"}))  # chunk containing the success frame
        for c in range(16, 20):  # after the success frame, incl. the release at frame 160
            self.assertEqual(rule_of(ref, c), ("post_success", {"neutral", "aftermath"}), c)
            self.assertEqual(ref["chunk_labels"][c]["primary"], "neutral")
        self.assertNotIn("success_default", {cl["rule"] for cl in ref["chunk_labels"]})
        for cl in ref["chunk_labels"]:
            self.assertIn(cl["primary"], cl["allowed"]); self.assertTrue(cl["scorable"])
            self.assertNotIn("failure_inducing", cl["allowed"])
        self.assertEqual(ref["anomalies"], [])

    def test_drop_then_regrasp_is_a_recovered_error(self):
        ep = FakeEpisode(n=300, success=True)
        ep.grasp("target_1", 50, 80, lift_from=60, cmd_close_until=85)
        ep.cols["observation.state"][85:120, 6] = 0.04
        ep.move(130, 200, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
        ep.grasp("target_1", 120, 210, lift_from=130).release(210)
        ep.cols["next.success"][200:, 0] = 1
        ref = build_reference(ep)
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp", "drop", "grasp", "release"])
        self.assertEqual((ref["failure_mode"], ref["cause"], ref["decisive_chunk"]), ("success", "grasp", 8))
        self.assertEqual(ref["mode_reason"], "success_recovered_drop")
        self.assertEqual(rule_of(ref, 8), ("other_event", {"failure_inducing"}))
        self.assertEqual(rule_of(ref, 10), ("idle", {"neutral"}))
        self.assertEqual(rule_of(ref, 11), ("regrasp", {"recovery"}))
        self.assertEqual(rule_of(ref, 15), ("advance_transporting", {"progress"}))
        self.assertEqual(rule_of(ref, 21), ("post_success", {"neutral", "aftermath"}))
        fi = [cl["chunk"] for cl in ref["chunk_labels"] if cl["primary"] == "failure_inducing"]
        self.assertEqual(fi, [8])

    def test_placing_release_before_the_predicate_is_progress(self):
        ep = FakeEpisode(n=200, success=True)
        ep.move(50, 120, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
        ep.grasp("target_1", 50, 125, lift_from=60).release(125)
        ep.cols["next.success"][128:, 0] = 1  # predicate fires once the object has settled
        ref = build_reference(ep)
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp", "release"])
        self.assertEqual(rule_of(ref, 12), ("place_release", {"progress"}))
        self.assertEqual(rule_of(ref, 13), ("post_success", {"neutral", "aftermath"}))
        self.assertEqual((ref["decisive_chunk"], ref["cause"]), (None, "unclear"))

    def test_close_on_nothing_then_grasp_is_recovered_unless_on_a_fixture(self):
        def make():
            ep = FakeEpisode(n=200, success=True)
            ep.contact("target_1", 40, 45)
            ep.cols["action"][44:60, 6] = 1.0; ep.cols["observation.state"][48:60, 6] = 0.001  # closed on nothing 48..59
            ep.cols["observation.state"][60:, 6] = 0.04
            ep.move(90, 150, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
            ep.grasp("target_1", 80, 160, lift_from=90)
            ep.cols["next.success"][150:, 0] = 1
            return ep
        ref = build_reference(make())
        self.assertEqual((ref["close_on_nothing"][0]["start"], ref["close_on_nothing"][0].get("kind")), (44, "attempt"))  # r4: the failed attempt starts at the target contact
        self.assertEqual((ref["failure_mode"], ref["cause"], ref["decisive_chunk"]), ("success", "grasp", 4))
        self.assertEqual(ref["mode_reason"], "success_recovered_close_on_nothing")
        self.assertEqual(rule_of(ref, 4), ("attempt_boundary", {"failure_inducing", "neutral"}))
        self.assertEqual(rule_of(ref, 7), ("regrasp", {"recovery"}))  # grasp last_before 79
        ep2 = make()
        ep2.cols["priv.gripper_static_contacts"][48:60, 0] = 1  # the closed gripper is pressing a fixture (knob)
        ref2 = build_reference(ep2)
        self.assertEqual((ref2["decisive_chunk"], ref2["cause"], ref2["mode_reason"]), (None, "unclear", "success"))
        self.assertNotIn("failure_inducing", rule_of(ref2, 4)[1])
        self.assertNotEqual(rule_of(ref2, 7)[0], "regrasp")

    def test_wrong_grasp_then_success(self):
        ep = FakeEpisode(n=250, success=True)
        ep.grasp("distractor_1", 33, 60, lift_from=40, cmd_close_until=62)  # wrong object, dropped
        ep.cols["observation.state"][63:, 6] = 0.04
        ep.move(130, 200, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
        ep.grasp("target_1", 120, 210, lift_from=130)
        ep.cols["next.success"][200:, 0] = 1
        ref = build_reference(ep)
        self.assertEqual((ref["failure_mode"], ref["cause"], ref["decisive_chunk"]), ("success", "sequencing_semantic", 3))
        self.assertEqual(ref["mode_reason"], "success_recovered_wrong_grasp")
        self.assertEqual(rule_of(ref, 3), ("other_event", {"failure_inducing"}))
        self.assertEqual(rule_of(ref, 4)[0], "pre_recovering")  # lifting the WRONG object earns no advance credit
        self.assertEqual(rule_of(ref, 6)[0], "pre_recovering")  # the distractor's drop (not a task object) is not drop_final
        self.assertEqual(rule_of(ref, 11), ("regrasp", {"recovery"}))
        ep2 = FakeEpisode(n=250, success=True)
        ep2.grasp("distractor_1", 33, 60, lift_from=40).release(60)  # put the wrong object back down
        ep2.cols["observation.state"][63:, 6] = 0.04
        ep2.move(130, 200, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
        ep2.grasp("target_1", 120, 210, lift_from=130)
        ep2.cols["next.success"][200:, 0] = 1
        ref2 = build_reference(ep2)
        self.assertEqual(rule_of(ref2, 6), ("wrong_release", {"recovery", "neutral", "progress"}))
        self.assertEqual(ref2["chunk_labels"][6]["primary"], "recovery")

    def test_two_object_task_credits_the_object_in_hand(self):
        ep = FakeEpisode(n=220, success=True)
        ep.meta["goal_state"] = [["in", "target_1", "basket_1_contain_region"], ["in", "distractor_1", "basket_1_contain_region"]]
        ep.cols["priv.target_mask"][:, 2] = 1  # both objects are task objects
        ep.move(50, 100, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
        ep.grasp("target_1", 50, 100, lift_from=60).release(100)  # first object placed
        ep.move(105, 140, (0.5, 0.3, 0.98), (0.3, -0.2, 0.93))  # approach the second object
        ep.move(150, 200, (0.3, -0.2, 0.93), (0.5, 0.3, 0.98))  # carry it to the basket
        ep.grasp("distractor_1", 140, 205, lift_from=150).release(205)
        ep.cols["next.success"][199:, 0] = 1
        ref = build_reference(ep)
        self.assertEqual(ref["target_candidates"], ["target_1", "distractor_1"])
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp", "release", "grasp", "release"])
        self.assertEqual(rule_of(ref, 10), ("place_release", {"progress"}))
        self.assertEqual(rule_of(ref, 11), ("advance_approach", {"progress"}))  # towards the next object
        self.assertEqual(rule_of(ref, 16), ("advance_transporting", {"progress"}))  # the second object is in hand
        self.assertEqual(rule_of(ref, 20), ("post_success", {"neutral", "aftermath"}))
        self.assertEqual((ref["decisive_chunk"], ref["cause"], ref["wrong_object_contacts"]), (None, "unclear", []))
        self.assertFalse(any("failure_inducing" in cl["allowed"] for cl in ref["chunk_labels"]))

    def test_success_without_predicate_is_flagged(self):
        ep = self.clean()
        ep.cols["next.success"][:] = 0  # relabelled success (exclusions.json) whose predicate never fired
        ref = build_reference(ep)
        self.assertIn("success_without_predicate", ref["anomalies"])
        self.assertFalse(any(cl["rule"] == "post_success" for cl in ref["chunk_labels"]))
        self.assertEqual(rule_of(ref, 16)[1], {"progress"})  # the release now reads as the placement

    def test_closing_motion_and_post_placement_closures_are_not_misses(self):
        ep = self.clean()
        ep.cols["action"][40:, 6] = 1.0
        ep.cols["observation.state"][42:50, 6] = 0.001  # aperture reads closed 42..49 (contact flags come on at 50): the grasp itself
        ref = build_reference(ep)
        self.assertEqual(ref["close_on_nothing"][0]["start"], 42)
        self.assertEqual((ref["decisive_chunk"], ref["cause"], ref["mode_reason"]), (None, "unclear", "success"))
        self.assertNotIn("other_event", {cl["rule"] for cl in ref["chunk_labels"]})
        ep2 = FakeEpisode(n=200, success=True)
        ep2.move(50, 120, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
        ep2.grasp("target_1", 50, 125, lift_from=60, cmd_close_until=199)  # dropped into the basket, command stays CLOSE
        ep2.cols["observation.state"][128:, 6] = 0.001  # the empty gripper closes fully afterwards
        ep2.cols["next.success"][130:, 0] = 1
        ref2 = build_reference(ep2)
        self.assertEqual([e["type"] for e in ref2["events"]], ["grasp", "drop"])
        self.assertEqual(ref2["close_on_nothing"], [])  # r3: the closure 3 frames after the drop is the same attempt
        self.assertEqual([(p["start"], p["after_drop"]) for p in ref2["post_slip_closure"]], [(128, 125)])
        self.assertEqual(rule_of(ref2, 12), ("drop_final", {"progress", "neutral"}))
        self.assertEqual((ref2["decisive_chunk"], ref2["cause"]), (None, "unclear"))  # no later grasp: not a recovered miss

    def test_fixture_motion_is_progress_when_the_task_asks_for_it(self):
        ep = FakeEpisode(n=200, success=True)
        ep.meta["goal_state"].append(["open", "top_drawer"])
        ep.meta["fixture_joint_names"] = ["top_drawer_joint"]
        ep.cols["priv.fixture_valid"][:, 0] = 1
        ep.cols["priv.fixture_qpos"][20:51, 0] = np.linspace(0.0, 0.1, 31); ep.cols["priv.fixture_qpos"][51:, 0] = 0.1
        ep.move(0, 100, (0.2, 0.0, 1.1), (0.2, 0.0, 1.1))  # arm still while the drawer opens (frames 20..50)
        ep.move(100, 130, (0.2, 0.0, 1.1), (0.5, 0.0, 0.93))
        ep.move(150, 180, (0.5, 0.0, 0.93), (0.5, 0.3, 0.98))
        ep.grasp("target_1", 140, 190, lift_from=150)
        ep.cols["next.success"][180:, 0] = 1
        ref = build_reference(ep)
        self.assertEqual(ref["fixture_motion"][0]["joint"], "top_drawer_joint")
        self.assertEqual(rule_of(ref, 0), ("idle", {"neutral"}))
        for c in (2, 3, 4):
            self.assertEqual(rule_of(ref, c), ("advance_fixture", {"progress"}), c)
        self.assertEqual(rule_of(ref, 7), ("idle", {"neutral"}))
        self.assertEqual(rule_of(ref, 10)[1], {"progress"})  # approach
        ep.meta["goal_state"] = ep.meta["goal_state"][:1]  # same motion, but the task does not ask for the drawer
        self.assertEqual(rule_of(build_reference(ep), 3), ("idle", {"neutral"}))
        ep.meta["goal_state"] = [["in", "target_1", "top_drawer_region"]]  # no open atom, but the goal region is in that drawer
        ref3 = build_reference(ep)
        self.assertIsNone(ref3["goal_slot"])
        self.assertEqual(rule_of(ref3, 3), ("advance_fixture", {"progress"}))
        ep.cols["priv.fixture_qpos"][20:51, 0] = np.linspace(0.0, 0.005, 31); ep.cols["priv.fixture_qpos"][51:, 0] = 0.005  # 5 mm jitter
        ref4 = build_reference(ep)
        self.assertTrue(ref4["fixture_motion"])  # still listed
        self.assertEqual(rule_of(ref4, 3), ("idle", {"neutral"}))  # but not task progress

    def test_failure_path_unchanged_by_success_rules(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 100, lift_from=60, cmd_close_until=110)
        ref = build_reference(ep)
        rules = {cl["rule"].split("+")[0] for cl in ref["chunk_labels"]}
        self.assertFalse(rules & {"post_success", "place_release", "drop_final", "wrong_release"})
        self.assertEqual(ref["cause"], "grasp")


if __name__ == "__main__":
    unittest.main()
