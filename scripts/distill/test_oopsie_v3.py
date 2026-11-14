"""Window coordinates and selective uncertainty supervision; no paid calls."""
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import oopsie_common as common
import oopsie_markdown as md
import oopsie_pipeline as pipeline
from test_oopsie_pipeline import answer, fixture


def proposed_failure(eid="O001"):
    value = answer(eid)
    value["segments"][0].update(failure=True, categories=["manipulation"], recovery="Inspect placement.",
        severity="low", resetability="minor_reset", review_required=True,
        uncertain_fields=["timing", "mechanism", "outcome", "recovery", "severity", "resetability"],
        uncertainty="Exact release timing and final support are unresolved.",
        observed_result="The caf\u00e9 object \U0001f916 is outside its destination.")
    return value


class V3Tests(unittest.TestCase):
    def test_supported_failure_survives_timing_uncertainty_but_prose_does_not(self):
        value = proposed_failure()
        text = md.render(value).replace("\n", "\r\n")
        exact, masks = md.target_with_masks(value, text)
        self.assertEqual(exact, text)
        self.assertEqual(md.parse(exact)[0], value)
        self.assertFalse(masks["has_unflagged_segment_targets"])
        self.assertTrue(masks["has_eligible_segment_targets"])
        def excluded(fragment):
            a = text.index(fragment)
            return any(a < r["end"] and a+len(fragment) > r["start"] for r in masks["assistant_excluded_char_ranges"])
        self.assertFalse(excluded("- Failure: Yes"))
        self.assertFalse(excluded("- Categories: manipulation"))
        for fragment in ("- Frames:", "- Action:", "- Severity:", "### Observed result", "caf\u00e9"):
            self.assertTrue(excluded(fragment), fragment)

    def test_uncertain_failure_cannot_become_a_positive_or_negative_target(self):
        value = proposed_failure()
        value["segments"][0]["uncertain_fields"].append("failure")
        text, masks = md.target_with_masks(value)
        a = text.index("- Failure: Yes")
        self.assertTrue(any(r["start"] <= a < r["end"] for r in masks["assistant_excluded_char_ranges"]))
        self.assertFalse(masks["has_eligible_segment_targets"])
        self.assertEqual(masks["segments"][0]["failure_teacher_loss_mask"], 0)

    def test_unknown_uncertainty_and_inconsistent_review_flags_are_rejected(self):
        for field in ("imaginary", "timing, timing"):
            text = md.render(proposed_failure()).replace("- Uncertain fields: timing, mechanism, outcome, recovery, severity, resetability", "- Uncertain fields: " + field)
            with self.assertRaises(ValueError):
                md.parse(text)
        with self.assertRaises(ValueError):
            md.parse(md.render(proposed_failure()).replace("- Review required: Yes", "- Review required: No"))

    def test_window_sampling_keeps_rate_endpoints_overlap_and_native_five_hz(self):
        for fps in (5, 12, 20, 30, 50):
            windows = pipeline.sampling_windows(round(49*fps), fps, 4, 48, 10, 1)
            self.assertEqual(windows[0][0], 0)
            self.assertEqual(windows[-1][1], round(49*fps))
            for start, end, frames in windows:
                self.assertEqual((frames[0], frames[-1]), (start, end-1))
                self.assertLessEqual(len(frames), 48)
                if end-start >= 9*fps:
                    self.assertGreaterEqual(len(frames), 36)
            self.assertTrue(all(b[0] < a[1] for a, b in zip(windows, windows[1:])))
        with self.assertRaisesRegex(ValueError, "instead of thinning"):
            pipeline.sampling_windows(1000, 20, 4, 32, 10, 1)

    def test_window_validation_uses_original_source_coordinates(self):
        value = proposed_failure("O001_W02")
        value["segments"][0].update(start_frame=100, end_frame=120)
        for group in [value["identity_check"], *value["segments"]]:
            for evidence in group["evidence"]:
                evidence["frame"] += 100
        episode = dict(id="O001_W02", n_frames=200, window_start_frame=100, window_end_frame=120,
                       annotation_schema="field_review_v3", sampled_frames=[100, 105, 119],
                       images=[dict(frame=f, camera="left_wrist") for f in (100, 105, 119)])
        common.validate_annotation(value, episode)
        value["segments"][0]["start_frame"] = 0
        with self.assertRaises(ValueError):
            common.validate_annotation(value, episode)

    def test_native_v3_collection_export_and_reload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/"run"
            manifest = fixture(root)
            manifest["config"].update(annotation_format="markdown", annotation_schema="field_review_v3")
            for episode in manifest["episodes"]:
                episode["annotation_schema"] = "field_review_v3"
            (root/"manifest.json").write_text(json.dumps(manifest))
            def post(url, provider, body, keys):
                if url.endswith("input_tokens"):
                    return dict(input_tokens=100)
                eid = re.search(r"- Episode: (O\d+)", body["input"][0]["content"][0]["text"])[1]
                return dict(status="completed", model=body["model"], usage=dict(input_tokens=100, output_tokens=100),
                            output=[dict(content=[dict(type="output_text", text=md.render(proposed_failure(eid)))])])
            with patch.object(pipeline.transport, "post", side_effect=post), patch.object(pipeline.transport, "credentials", return_value={"openai":"fixture"}):
                result = pipeline.collect(root, 10, teachers=["sol"])
            self.assertEqual(result["validated"], 3)
            self.assertEqual(result["segment_counts"]["sol:eligible:failure"], 3)
            out = Path(temp)/"export"
            pipeline.export(root, out)
            _, _, rows = common.load_export(out)
            self.assertTrue(rows[0]["supervision"]["has_eligible_segment_targets"])
            self.assertFalse(rows[0]["supervision"]["has_unflagged_segment_targets"])


if __name__ == "__main__":
    unittest.main()
