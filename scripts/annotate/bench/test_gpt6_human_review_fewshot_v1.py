import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "gpt6_human_review_fewshot_v1", HERE / "gpt6_human_review_fewshot_v1.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GPT6HumanReviewFewshotTests(unittest.TestCase):
    def test_sampling_includes_first_and_last_frame(self):
        self.assertEqual(MODULE.sampled_indices(10, 4), [0, 4, 8, 9])
        self.assertEqual(MODULE.sampled_indices(9, 4), [0, 4, 8])

    def test_remaps_complete_human_segments_to_local_frames(self):
        segments = [
            {"start": 0, "end": 5, "text": "approach", "classification": "progress",
             "failure_type": "unknown"},
            {"start": 5, "end": 10, "text": "miss", "classification": "failure",
             "failure_type": "missed_target"},
        ]
        remapped = MODULE.remap_segments(segments, [0, 4, 8, 9])
        self.assertEqual([(s["start"], s["end"]) for s in remapped], [(0, 2), (2, 4)])
        self.assertEqual(remapped[1]["failure_type"], "missed_target")

    def test_turn_one_contains_demonstrations_before_unseen_target(self):
        prompt = MODULE.prompt_one("R001")
        for ident in MODULE.EXAMPLE_IDS:
            self.assertIn(f"examples/{ident}/manifest.json", prompt)
        self.assertIn("study every demonstration as an input/output pair", prompt)
        self.assertIn("human_label.json", prompt)
        self.assertIn("gpt6_fewshot_observation.json", prompt)
        self.assertIn("no numerical relationship to R001", prompt)

    def test_fewshot_candidate_uses_distinct_version(self):
        meta = {"id": "R001", "task": "pick up butter", "fps": 20, "n_frames": 2}
        candidate = {
            "version": MODULE.VERSION,
            "model_family": MODULE.MODEL,
            "id": "R001",
            "task": "pick up butter",
            "fps": 20,
            "episode_outcome": "unknown",
            "target_description": "butter box",
            "summary": "approaches the butter",
            "segments": [{
                "start": 0, "end": 2, "text": "approaches", "classification": "progress",
                "failure_type": "unknown", "confidence": 0.7, "note": "",
                "evidence_frames": [0, 1],
            }],
            "events": [],
            "trajectory_note": "",
        }
        self.assertIs(MODULE.validate_candidate(candidate, meta), candidate)
        candidate["version"] = "gpt6_human_review_v1"
        with self.assertRaisesRegex(ValueError, "version"):
            MODULE.validate_candidate(candidate, meta)


if __name__ == "__main__":
    unittest.main()
