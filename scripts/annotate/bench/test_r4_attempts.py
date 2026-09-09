"""Reference r4: failed grasp attempts (a CLOSE run whose aperture collapses next to / on the target without a hold)."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oracle_reference import build_reference  # noqa: E402
from test_oracle_reference import FakeEpisode  # noqa: E402


def close_and_reopen(ep, a, e, lo=0.005):
    """CLOSE command on [a, e]; aperture falls linearly from 4 cm at a to `lo` at e, back to 4 cm two frames after e."""
    ep.cols["action"][a:e + 1, 6] = 1.0
    ap = ep.cols["observation.state"][:, 6]
    for i in range(a, e + 1):
        ap[i] = 0.04 + (lo - 0.04) * (i - a) / max(e - a, 1)
    ap[e + 1] = lo
    ap[e + 2:] = 0.04


def labels(ref):
    return {cl["chunk"]: (cl["allowed"], cl["rule"]) for cl in ref["chunk_labels"]}


class AttemptTests(unittest.TestCase):
    def test_contact_then_collapse_and_instant_reopen_is_an_attempt(self):
        ep = FakeEpisode()
        ep.contact("target_1", 100, 106)          # fingers touch the target while closing
        close_and_reopen(ep, 98, 109)             # closed on nothing for a single frame, then re-opened
        ref = build_reference(ep)
        self.assertEqual(len(ref["attempts"]), 1)
        x = ref["attempts"][0]
        self.assertEqual((x["start"], x["end"], x["chunk"]), (100, 109, 10))
        self.assertTrue(x["contact"])
        self.assertIn("failure_inducing", labels(ref)[10][0])
        self.assertIn("failure_inducing", labels(ref)[10][0])
        self.assertEqual(ref["failure_mode"], "missed_grasp")
        self.assertEqual(ref["decisive_chunk"], 10)
        self.assertEqual(ref["cause"], "grasp")
        self.assertTrue(any(c.get("kind") == "attempt" for c in ref["close_on_nothing"]))

    def test_attempt_spanning_two_chunks_marks_both(self):
        ep = FakeEpisode()
        ep.contact("target_1", 106, 112)
        close_and_reopen(ep, 104, 116)
        ref = build_reference(ep)
        self.assertEqual(ref["attempts"][0]["chunks"], [10, 11])
        self.assertIn("failure_inducing", labels(ref)[10][0])
        self.assertIn("neutral", labels(ref)[11][0])

    def test_collapse_far_from_target_without_contact_is_not_an_attempt(self):
        ep = FakeEpisode()
        ep.move(0, 50, (0.2, 0.0, 1.1), (0.1, 0.4, 1.1))   # 45 cm away from the target
        close_and_reopen(ep, 98, 109)
        ref = build_reference(ep)
        self.assertEqual(ref["attempts"], [])

    def test_collapse_near_target_without_contact_is_an_attempt(self):
        ep = FakeEpisode()                                 # default approach ends 3 cm above the target
        close_and_reopen(ep, 98, 109)
        ref = build_reference(ep)
        self.assertEqual(len(ref["attempts"]), 1)
        self.assertFalse(ref["attempts"][0]["contact"])

    def test_run_with_a_hold_is_a_slip_not_an_attempt(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 100, 106, lift_from=103, cmd_close_until=112, aperture=0.02)
        ap = ep.cols["observation.state"][:, 6]
        ap[107:111] = np.linspace(0.015, 0.003, 4)
        ap[111:] = 0.003
        ref = build_reference(ep)
        self.assertEqual(ref["attempts"], [])
        self.assertEqual([e["type"] for e in ref["events"]], ["grasp", "drop"])

    def test_closure_touching_a_fixture_is_not_an_attempt(self):
        ep = FakeEpisode()
        ep.cols["priv.gripper_fixture_contacts"][100:108, 0] = 1  # closing on a knob / handle
        close_and_reopen(ep, 98, 109)
        ref = build_reference(ep)
        self.assertEqual(ref["attempts"], [])

    def test_table_brush_during_the_closure_does_not_disqualify(self):
        ep = FakeEpisode()
        ep.contact("target_1", 100, 106)
        ep.cols["priv.gripper_static_contacts"][102, 0] = 1  # one frame of fingertip on the table (goals8 t6 ep 0, frame 181)
        close_and_reopen(ep, 98, 109)
        ref = build_reference(ep)
        self.assertEqual(len(ref["attempts"]), 1)
        self.assertEqual(ref["attempts"][0]["end"], 109)  # clipped to the CLOSE run even though the minimum is at 110

    def test_two_attempts_then_success_grasp(self):
        ep = FakeEpisode(success=True)
        ep.contact("target_1", 100, 105)
        close_and_reopen(ep, 98, 108)
        ep.contact("target_1", 130, 135)
        close_and_reopen(ep, 128, 138)
        ep.grasp("target_1", 160, 299, lift_from=165, cmd_close_until=299, aperture=0.02)
        ep.cols["next.success"][290:, 0] = 1
        ref = build_reference(ep)
        self.assertEqual([x["chunk"] for x in ref["attempts"]], [10, 13])
        self.assertIn("failure_inducing", labels(ref)[10][0])
        self.assertIn("failure_inducing", labels(ref)[13][0])
        self.assertEqual(labels(ref)[15][0], ["recovery"])  # the closing action (frames 157-159) precedes the hold at 160
        self.assertEqual(ref["reference_version"], "r6")


if __name__ == "__main__":
    unittest.main()
