"""Markdown teacher outputs, native text masks, and lossless format migration."""
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
import score_oopsie
from test_oopsie_pipeline import fixture, answer


class MarkdownTests(unittest.TestCase):
    def test_round_trip_preserves_unicode_evidence_and_nullable_fields(self):
        value = answer()
        value["segments"][0]["what_happened"] = 'The robot moves the café object 🤖.\nIts outcome stays visible.'
        value["identity_check"]["requested_object"] = "A cup\nwith a handle"
        self.assertEqual(md.parse(md.render(value))[0], value)

    def test_uncertain_segment_and_identity_masks_are_exact_unicode_sections(self):
        value = answer(flagged=True)
        value["identity_check"].update(match_status="unresolved", uncertainty="Ambiguous café 🤖 identity")
        text, supervision = md.target_with_masks(value)
        self.assertFalse(supervision["has_unflagged_segment_targets"])
        identity, segment = supervision["assistant_excluded_char_ranges"]
        self.assertTrue(text[identity["start"]:identity["end"]].startswith("## Identity"))
        self.assertTrue(text[segment["start"]:segment["end"]].startswith("## Segment 1"))
        self.assertEqual(segment["end"], len(text))
        self.assertFalse(supervision["human_verified"])

    def test_native_crlf_text_and_offsets_are_preserved(self):
        value = answer(flagged=True)
        text = md.render(value).replace("\n", "\r\n")
        exact, supervision = md.target_with_masks(value, text)
        self.assertEqual(exact, text)
        self.assertEqual(md.parse(text)[0], value)
        span = supervision["assistant_excluded_char_ranges"][0]
        self.assertEqual(text[span["start"]:], text[text.index("## Segment 1"):])

    def test_invalid_fields_and_noncontiguous_segments_are_rejected(self):
        text = md.render(answer())
        for invalid in (text.replace("- Failure: No", "- Failure: Maybe"),
                        text.replace("## Segment 1", "## Segment 2"),
                        text.replace("- Categories: None", "- Categories: None\n- Extra: value"),
                        "```markdown\n" + text + "```", text.replace("- Action ID: a1", "- Action ID: a1\n- Action ID: a2")):
            with self.subTest(invalid=invalid[:60]), self.assertRaises(ValueError):
                md.parse(invalid)

    def test_target_validation_rejects_changed_values(self):
        value = answer()
        with self.assertRaisesRegex(ValueError, "changed"):
            md.target_with_masks(value, md.render(value).replace("transport", "release"))

    def test_native_markdown_collection_export_and_reload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "run"
            manifest = fixture(root)
            manifest["config"]["annotation_format"] = "markdown"
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            native = {}

            def fake_post(url, provider, body, keys):
                if url.endswith("input_tokens"):
                    return dict(input_tokens=100)
                self.assertEqual(body["text"]["format"]["type"], "text")
                metadata = body["input"][0]["content"][0]["text"]
                self.assertNotIn('"episode_id"', metadata)
                eid = re.search(r"- Episode: (O\d+)", metadata)[1]
                native[eid] = md.render(answer(eid)).replace("\n", "\r\n")
                return dict(status="completed", model=body["model"], usage=dict(input_tokens=100, output_tokens=100),
                            output=[dict(content=[dict(type="output_text", text=native[eid])])])

            with patch.object(pipeline.transport, "post", side_effect=fake_post), \
                 patch.object(pipeline.transport, "credentials", return_value={"openai": "fixture"}):
                result = pipeline.collect(root, 10, teachers=["sol"])
            self.assertEqual(result["validated"], 3)
            self.assertFalse((root / "traces/O001_sol/annotation.json").exists())
            self.assertEqual((root / "traces/O001_sol/annotation.md").read_bytes().decode(), native["O001"])
            out = Path(temp) / "export"
            pipeline.export(root, out)
            for split in ("train", "development", "test"):
                _, _, rows = common.load_export(out, split)
                self.assertEqual(rows[0]["target_format"], "markdown")
                self.assertEqual(rows[0]["messages"][-1]["content"], native[rows[0]["episode_id"]])

    def test_independent_reference_index_uses_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "references.md").write_text(
                "# Independent human references\n\n- Kind: independent_human\n"
                "- Reviewers: Reviewer A; Reviewer B\n- Blind to teacher: Yes\n"
                "- Manifest SHA-256: actual-manifest-hash\n\n## Episodes\n\n- O007: O007.md | annotation-hash\n", encoding="utf-8")
            index = score_oopsie.reference_index(root)
            self.assertEqual(index["reviewers"], ["Reviewer A", "Reviewer B"])
            self.assertTrue(index["blind_to_teacher"])
            self.assertEqual(index["episodes"]["O007"]["annotation"], "O007.md")


if __name__ == "__main__":
    unittest.main()
