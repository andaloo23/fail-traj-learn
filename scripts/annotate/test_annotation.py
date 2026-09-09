"""CPU regression checks: python -m unittest discover -s scripts/annotate -p 'test_*.py'."""
import json
import unittest
import io
from contextlib import redirect_stdout
from unittest.mock import patch

import numpy as np

from aggregate import aggregate, merge_refinement, quality_flags
from common import corrected_success
from render import build_tiles
from schema import ParseError, parse_annotation
import eval_vs_oracle


def answer(label="neutral", **overrides):
    raw = {"outcome": "failure", "segments": [{"start": 0, "end": 2, "label": label}]}
    raw.update(overrides)
    return raw


def parse(raw):
    return parse_annotation(json.dumps(raw), 3)


class AnnotationChecks(unittest.TestCase):
    def test_evaluator_reports_missing_predictions_and_recovered_successes(self):
        def record(success=False, error=None, source="vlm"):
            ann = aggregate([parse(answer(decisive_error=error))], 3)
            return {"success": success, "source": source, "annotation": ann}

        reference = {("test", 0): record(error=1), ("test", 1): record(error=1),
                     ("test", 2): record(success=True, error=1),
                     ("test", 3): record(success=True)}
        pred = {("test", 0): {"success": False, "source": "vlm_failed"},
                ("test", 2): record(success=True, error=1),
                ("test", 3): record(success=True, source="oracle_default")}
        stream = io.StringIO()
        with patch("sys.argv", ["eval", "--pred", "p", "--ref", "r"]), \
                patch.object(eval_vs_oracle, "list_datasets", return_value=["test"]), \
                patch.object(eval_vs_oracle, "load", side_effect=[pred, reference]), redirect_stdout(stream):
            eval_vs_oracle.main()
        result = json.loads(stream.getvalue())
        self.assertEqual(result["missing_records"], 1)
        self.assertEqual(result["failed_annotations"], 1)
        self.assertEqual(result["missing_tstar"], 2)
        self.assertEqual(result["tstar_within_1_including_missing"], 0)
        self.assertEqual(result["successes"], 0)

    def test_rejects_temporal_repairs(self):
        for raw in [answer(decisive_error=8), answer(decisive_error=1.5),
                    answer(segments=[{"start": 1, "end": 2, "label": "neutral"}]),
                    answer(segments=[{"start": 2, "end": 0, "label": "neutral"}]),
                    answer(segments=[{"start": 0, "end": 1, "label": "neutral"},
                                     {"start": 1, "end": 2, "label": "progress"}])]:
            with self.subTest(raw=raw), self.assertRaises(ParseError):
                parse(raw)

    def test_single_label_votes_are_retained(self):
        result = aggregate([parse(answer())] * 3 + [parse(answer("progress"))] * 2, 3)
        self.assertEqual(result["k"], 5)
        self.assertEqual(result["chunk_label"], ["neutral"] * 3)
        self.assertEqual(result["chunk_q"], [0.6] * 3)

    def test_failed_samples_and_ties_abstain(self):
        result = aggregate([parse(answer())] * 2, 3, n_attempted=5)
        self.assertEqual(result["chunk_q"], [0.0] * 3)
        self.assertEqual(result["n_invalid"], 3)
        result = aggregate([parse(answer()), parse(answer("progress"))], 3)
        self.assertEqual(result["chunk_q"], [0.0] * 3)

    def test_refinement_empty_and_null_safe(self):
        agg = aggregate([parse(answer())], 3)
        for refined in ([], [{}], [{"error": "invalid"}]):
            self.assertEqual(merge_refinement(agg, refined)["landmarks"], agg["landmarks"])

    def test_refinement_preserves_landmarks_outside_window(self):
        agg = aggregate([parse(answer(decisive_error=0, visible_failure=2))], 3)
        result = merge_refinement(agg, [{"decisive_error": 1, "visible_failure": 1}], window=(0, 1))
        self.assertEqual(result["landmarks"]["visible_failure"]["value"], 2)
        self.assertIn("decisive_error_outside_failure_segment", quality_flags(result))

    def test_outcome_correction(self):
        self.assertTrue(corrected_success("full_shift16__t3", 28, False))
        self.assertFalse(corrected_success("full_shift16__t3", 27, False))

    def test_grouping_does_not_omit_chunks(self):
        class Episode:
            n_chunks = 5
            chunks = [(10 * c, 10 * c + 10) for c in range(5)]
            seen = []

            def frame(self, i):
                self.seen.append(i)
                im = np.zeros((256, 256, 3), dtype=np.uint8)
                return im, im

        episode = Episode()
        tiles = build_tiles(episode, max_tiles=2)
        self.assertEqual(len(tiles), 2)
        self.assertEqual(episode.seen, [0, 9, 10, 19, 20, 29, 30, 39, 40, 49])


if __name__ == "__main__":
    unittest.main()
