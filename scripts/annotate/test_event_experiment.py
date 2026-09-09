import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from event_experiment import export_window, parse_events, sampled_frames, summarize, window_plan


class EventExperimentTests(unittest.TestCase):
    def test_scan_covers_episode_with_overlap_and_tail(self):
        for n in (1, 3, 4, 5, 11, 28):
            windows = window_plan(n)
            self.assertEqual(set(range(n)), {c for lo, hi in windows for c in range(lo, hi + 1)})
            self.assertEqual(len(windows), len(set(windows)))
        with self.assertRaises(ValueError):
            window_plan(28, 4, 4)

    def test_sampling_retains_chunk_end_and_next_start(self):
        frames = sampled_frames([(100, 110), (110, 120), (120, 130), (130, 140)], 0, 3, 2)
        self.assertTrue({109, 110, 119, 120, 129, 130, 139}.issubset(frames))

    def test_export_cannot_access_outcome_or_privileged_columns(self):
        class Episode:
            chunks = [(0, 10)]
            fps = 20

            def frame(self, i):
                return np.zeros((256, 256, 3), dtype=np.uint8), np.zeros((256, 256, 3), dtype=np.uint8)

            def __getattr__(self, name):
                raise AssertionError(f"Forbidden episode access: {name}")

        with tempfile.TemporaryDirectory() as tmp:
            bundle = export_window(Episode(), 0, 0, 2, Path(tmp))
            self.assertEqual(bundle["frames"][-1], 9)
            self.assertTrue((Path(tmp) / "frame_000009.png").exists())

    def test_parser_rejects_unshown_or_reversed_frames(self):
        for a, b in ((1, 4), (4, 2), (True, 4)):
            raw = {"status": "observed", "events": [{"type": "detachment", "last_before_frame": a, "first_after_frame": b}]}
            with self.assertRaises(ValueError):
                parse_events(json.dumps(raw), [0, 2, 4])

    def test_reference_is_partial_and_missing_predictions_are_visible(self):
        ref = {"chunk": 12}
        chunks = [(i * 10, i * 10 + 10) for i in range(28)]
        empty = summarize([], ref, chunks)
        self.assertFalse(empty["reference_check"]["any_bracket_overlaps_reference_chunk"])
        row = {"window": [10, 13], "parsed": {"events": [{"type": "detachment", "last_before_frame": 128, "first_after_frame": 130}]}}
        result = summarize([row], ref, chunks)
        self.assertTrue(result["reference_check"]["any_bracket_overlaps_reference_chunk"])


if __name__ == "__main__":
    unittest.main()
