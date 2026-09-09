import json
import unittest

from local_segmenter import validate
from segmentation_lab import parse_states
from combine_local_evidence import transitions, agree_events


class SegmentationLabTests(unittest.TestCase):
    def test_interleaved_scan_errors_cannot_create_an_event(self):
        def track(items):
            return [{"frame": f, "state": s, "support": 1.0} for f, s in items]
        a = track([(100, "held"), (110, "held"), (115, "empty"), (120, "held"), (125, "empty"), (130, "empty")])
        b = track([(102, "held"), (112, "held"), (117, "empty"), (122, "held"), (127, "empty"), (132, "empty")])
        events = agree_events({"a": a, "b": b})
        self.assertEqual(len(events), 1)
        self.assertEqual((events[0]["last_before_frame"], events[0]["first_after_frame"]), (122, 125))

    def test_isolated_misread_does_not_create_false_loss(self):
        states = [{"frame": f, "state": s, "support": 1.0} for f, s in
                  [(0, "empty"), (5, "empty"), (10, "held"), (15, "held"),
                   (20, "empty"), (25, "held"), (30, "empty"), (35, "held"), (40, "empty"), (45, "empty")]]
        events = transitions(states)
        self.assertEqual([(e["event"], e["last_before_frame"], e["first_after_frame"]) for e in events],
                         [("grasp", 5, 10), ("loss_or_release", 35, 40)])

    def test_state_rows_cannot_skip_or_reorder_frames(self):
        for rows in ([{"frame": 1, "state": "held"}],
                     [{"frame": 2, "state": "empty"}, {"frame": 1, "state": "held"}]):
            with self.assertRaises(ValueError):
                parse_states(json.dumps({"states": rows}), [1, 2])

    def test_unknown_state_is_not_silently_repaired(self):
        with self.assertRaises(ValueError):
            parse_states('{"states":[{"frame":1,"state":"probably"}]}', [1])

    def test_local_event_must_use_observed_frames(self):
        row = {"label": "failure_inducing", "event": "loss", "last_before_frame": 120, "first_after_frame": 130}
        self.assertEqual(validate(json.dumps(row), [120, 125, 130]), row)
        with self.assertRaises(ValueError):
            validate(json.dumps(row), [120, 125])

    def test_uncertainty_is_preserved(self):
        row = {"label": "uncertain", "event": "none", "last_before_frame": None, "first_after_frame": None}
        self.assertEqual(validate(json.dumps(row), [0])["label"], "uncertain")


if __name__ == "__main__":
    unittest.main()
