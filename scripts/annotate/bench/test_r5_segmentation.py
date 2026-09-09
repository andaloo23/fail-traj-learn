"""Regression cases for mixed events, attempt boundaries, and recovery credit."""
import unittest

from oracle_reference import build_reference
from oracle_labels import frame_table
from test_oracle_reference import FakeEpisode
from test_r4_attempts import close_and_reopen


class SegmentationTests(unittest.TestCase):
    def test_short_slip_across_boundary_never_earns_positive_credit(self):
        for start in (76, 79, 80):
            with self.subTest(start=start):
                ep = FakeEpisode()
                ep.grasp("target_1", 50, 65, lift_from=55, cmd_close_until=70)
                ep.grasp("target_1", start, start + 3, lift_from=start, cmd_close_until=start + 8)
                ep.move(240, 299, (0.5, 0, 0.93), (0.5, 0.3, 1.1))
                ep.grasp("target_1", 240, 299, lift_from=245, cmd_close_until=299)
                ref = build_reference(ep)
                for c in range((start - 1) // 10, (start + 3) // 10 + 1):
                    self.assertFalse({"progress", "recovery"} & set(ref["chunk_labels"][c]["allowed"]))
                self.assertEqual(ref["chunk_labels"][23]["primary"], "recovery")

    def test_sustained_carry_before_later_drop_keeps_progress(self):
        ep = FakeEpisode()
        ep.move(60, 120, (0.5, 0, 1.0), (0.5, 0.3, 1.2))
        ep.grasp("target_1", 55, 125, lift_from=60, cmd_close_until=130)
        self.assertEqual(build_reference(ep)["chunk_labels"][9]["primary"], "progress")

    def test_retry_approach_is_neutral_even_before_eventual_grasp(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 65, lift_from=55, cmd_close_until=70)
        ep.move(90, 110, (0.7, 0, 0.93), (0.5, 0, 0.93))
        ep.move(240, 299, (0.5, 0, 0.93), (0.5, 0.3, 1.1))
        ep.grasp("target_1", 240, 299, lift_from=245, cmd_close_until=299)
        cl = build_reference(ep)["chunk_labels"][9]
        self.assertEqual(cl["rule"], "retry_motion")
        self.assertEqual(cl["allowed"], ["neutral"])

    def test_regrasp_then_drop_in_same_chunk_is_not_certain_recovery(self):
        for success in (False, True):
            with self.subTest(success=success):
                ep = FakeEpisode(success=success)
                ep.grasp("target_1", 50, 65, lift_from=55, cmd_close_until=70)
                ep.grasp("target_1", 132, 137, lift_from=133, cmd_close_until=142)
                ep.grasp("target_1", 240, 299, lift_from=245, cmd_close_until=299)
                if success:
                    ep.cols["next.success"][290:] = 1
                ref = build_reference(ep)
                cl = ref["chunk_labels"][13]
                self.assertEqual(cl["rule"], "failed_acquisition")
                self.assertEqual(set(cl["allowed"]), {"failure_inducing"})
                df = frame_table(ref, 0)
                self.assertEqual(df.loc[130, "q"], 1.0)
                self.assertEqual(df.loc[130, "label"], "failure_inducing")

    def test_initial_grasp_and_drop_has_no_positive_credit(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 52, 57, lift_from=53, cmd_close_until=62)
        cl = build_reference(ep)["chunk_labels"][5]
        self.assertEqual(set(cl["allowed"]), {"failure_inducing"})

    def test_one_frame_attempt_overlap_is_uncertain_but_full_chunk_is_failure(self):
        ep = FakeEpisode()
        ep.contact("target_1", 179, 186)
        close_and_reopen(ep, 177, 189)
        ref = build_reference(ep)
        self.assertEqual(ref["decisive_chunk"], 17)
        self.assertEqual(ref["chunk_labels"][17]["rule"], "attempt_boundary")
        self.assertEqual(ref["chunk_labels"][17]["primary"], "neutral")
        self.assertEqual(set(ref["chunk_labels"][17]["allowed"]), {"failure_inducing", "neutral"})
        self.assertEqual(ref["chunk_labels"][18]["allowed"], ["failure_inducing"])
        self.assertLess(frame_table(ref, 0).loc[179, "q"], 1)

    def test_later_grasp_does_not_turn_idle_into_recovery(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 65, lift_from=55, cmd_close_until=70)
        ep.move(240, 299, (0.5, 0, 0.93), (0.5, 0.3, 1.1))
        ep.grasp("target_1", 240, 299, lift_from=245, cmd_close_until=299)
        ref = build_reference(ep)
        self.assertEqual(ref["chunk_labels"][10]["allowed"], ["neutral"])

    def test_unexplained_motion_before_regrasp_is_not_primary_recovery(self):
        ep = FakeEpisode()
        ep.grasp("target_1", 50, 65, lift_from=55, cmd_close_until=70)
        ep.move(90, 130, (0.5, 0, 0.93), (0.7, 0, 0.93))
        ep.grasp("target_1", 240, 299, lift_from=245, cmd_close_until=299)
        cl = build_reference(ep)["chunk_labels"][10]
        self.assertEqual(cl["rule"], "pre_recovering")
        self.assertEqual(cl["primary"], "neutral")
        self.assertEqual(cl["allowed"], ["neutral"])


if __name__ == "__main__":
    unittest.main()
