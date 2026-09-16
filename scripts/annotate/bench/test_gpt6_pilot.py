import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("gpt6_pilot", HERE / "gpt6_pilot.py")
PILOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PILOT)


class PilotChecks(unittest.TestCase):
    def setUp(self):
        self.ref = {
            "chunks": [[i, i + 10] for i in range(0, 100, 10)],
            "target_slot": "target", "failure_mode": "drop_transport",
            "events": [
                {"type": "grasp", "last_before": 20, "first_after": 21},
                {"type": "drop", "last_before": 60, "first_after": 61},
            ],
            "held_runs": [{"start": 22, "end": 60, "state": "held", "object": "target"}],
            "close_on_nothing": [], "attempts": [], "collisions": [], "wrong_object_contacts": [],
            "stage_frames": {"reached": 18, "grasped": 21, "lifted": 30, "transported": 45, "placed": -1},
        }

    def test_drop_support_and_timing(self):
        seg = {"start_frame": 55, "end_frame_exclusive": 70}
        self.assertEqual(PILOT.check_claim(self.ref, seg, "events", "slip_drop")[0], "supported")
        seg = {"start_frame": 0, "end_frame_exclusive": 10}
        self.assertEqual(PILOT.check_claim(self.ref, seg, "events", "slip_drop")[0], "contradicted")

    def test_transport_needs_target_hold(self):
        seg = {"start_frame": 30, "end_frame_exclusive": 50}
        self.assertEqual(PILOT.check_claim(self.ref, seg, "events", "controlled_transport")[0], "supported")
        self.ref["held_runs"][0]["object"] = "distractor"
        self.assertEqual(PILOT.check_claim(self.ref, seg, "events", "controlled_transport")[0], "contradicted")

    def test_collision_with_drop_requires_both(self):
        self.ref["collisions"] = [{"start": 45, "end": 48}]
        seg = {"start_frame": 40, "end_frame_exclusive": 70}
        status, _ = PILOT.check_claim(self.ref, seg, "failure_subtypes", "transport.collision_with_drop")
        self.assertEqual(status, "supported")


if __name__ == "__main__":
    unittest.main()
