"""Guard against treating NVIDIA's invalid-clip normal fallback as a negative label."""
import json
from pathlib import Path
import tempfile
import unittest

from check_flora_results import check, check_rubric, rubric_samples_from_manifest


class DenseOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.jobs = self.root / "jobs.jsonl"
        self.jobs.write_text(json.dumps(dict(id="R001")) + "\n")
        self.output = self.root / "dense.jsonl"

    def result(self, rows):
        self.output.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return check(self.output, self.jobs)

    def row(self):
        return dict(id="R001", clips=[dict(valid=True)], invalid_clips=0,
                    num_frames=3, frame_scores=[1, 2, 3])

    def test_valid_predictions_remain_unverified_and_not_training_ready(self):
        report = self.result([self.row()])
        self.assertTrue(report["structurally_valid"])
        self.assertFalse(report["human_verified"])
        self.assertFalse(report["training_ready"])

    def test_normal_fallback_for_invalid_clip_is_rejected(self):
        row = self.row()
        row.update(clips=[dict(valid=False)], invalid_clips=1, frame_scores=[3, 3, 3])
        self.assertFalse(self.result([row])["structurally_valid"])

    def test_invalid_flag_is_checked_even_if_count_says_zero(self):
        row = self.row()
        row["clips"][0]["valid"] = False
        self.assertFalse(self.result([row])["structurally_valid"])

    def test_partial_job_and_duplicate_outputs_are_rejected(self):
        self.assertFalse(self.result([])["structurally_valid"])
        self.assertFalse(self.result([self.row(), self.row()])["structurally_valid"])

    def test_incomplete_frame_coverage_is_rejected(self):
        row = self.row()
        row["frame_scores"].pop()
        self.assertFalse(self.result([row])["structurally_valid"])


class RubricOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.jobs = self.root / "jobs.jsonl"
        self.jobs.write_text(json.dumps(dict(id="R001", task="Put the cup on the tray.", rubric=[
            dict(action="Complete the instruction", grading=[dict(points=0.0), dict(points=1.0)])])) + "\n")
        self.output = self.root / "rubric.jsonl"

    def row(self):
        return dict(id="R001", task="Put the cup on the tray.", steps=["Complete the instruction"],
                    scores=[1.0], total=1.0, medoid_sample=0, parsed_samples=1,
                    samples=[dict(parsed=True, scores=[1.0], answer="ANSWER: [1.0]",
                                  thinking="The cup is visibly placed on the tray.")])

    def result(self, rows):
        self.output.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return check_rubric(self.output, self.jobs)

    def test_complete_reasoning_and_scores_pass_without_human_verification(self):
        report = self.result([self.row()])
        self.assertTrue(report["structurally_valid"])
        self.assertFalse(report["human_verified"])

    def test_missing_reasoning_is_rejected(self):
        row = self.row()
        row["samples"][0].pop("thinking")
        self.assertFalse(self.result([row])["structurally_valid"])

    def test_upstream_clamping_cannot_hide_invalid_raw_score(self):
        row = self.row()
        row["samples"][0]["answer"] = "ANSWER: [2.0]"
        self.assertFalse(self.result([row])["structurally_valid"])

    def test_truncated_answer_and_invalid_selection_are_rejected(self):
        row = self.row()
        row.update(medoid_sample=None, parsed_samples=0)
        row["samples"][0].update(answer="", parsed=False)
        self.assertFalse(self.result([row])["structurally_valid"])


class RubricManifestTests(unittest.TestCase):
    def expected(self, manifest):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder/'run.json').write_text(json.dumps(manifest))
            return rubric_samples_from_manifest(folder/'rubric.jsonl')

    def test_reference_default_requires_nine_samples(self):
        self.assertEqual(self.expected(dict(command=['python','--keep-thinking'],
                                            reference_batch_defaults=True)),9)

    def test_legacy_explicit_single_sample_is_preserved(self):
        self.assertEqual(self.expected(dict(command=['python','--num-samples','1'])),1)

    def test_missing_configuration_does_not_infer_sample_count_from_predictions(self):
        with self.assertRaisesRegex(ValueError,'expected rubric sample count'):
            self.expected(dict(command=['python']))


if __name__ == "__main__":
    unittest.main()
