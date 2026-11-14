"""Offline tests of real-data provenance, splits, collection, and loss contracts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oopsie_common as common
import oopsie_pipeline as pipeline
import score_oopsie
from test_annotate_trajectories import annotation, segment


def fixture(root):
    cfg = common.read(common.ROOT / "configs/oopsie_qwen7b.json")
    cfg["max_output_tokens"] = 1000
    root.mkdir()
    (root / "prompt.txt").write_text("Return annotation JSON.", encoding="utf-8")
    episodes = []
    for i, split in enumerate(("train", "development", "test"), 1):
        eid = f"O{i:03d}"
        images = []
        for frame in (0, 5, 19):
            relative = f"images/{eid}/{frame}.jpg"
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fixture image bytes; tests do not decode")
            images.append(dict(frame=frame, seconds=frame/20, camera="left_wrist", path=relative))
        episodes.append(dict(id=eid, release_path=f"labs/lab{i}/{eid}.h5", lab=f"lab{i}", split=split,
                             task="Move object", n_frames=20, fps=20, sampled_frames=[0, 5, 19],
                             cameras=[dict(camera="left_wrist", description="left arm wrist camera")], images=images))
    manifest = dict(format="oopsie_distillation_v1", repo=common.REPO_ID, revision="pinned",
                    config=cfg, episodes=episodes,
                    files={p.relative_to(root).as_posix(): common.sha(p) for p in root.rglob("*") if p.is_file()})
    common.write(root / "manifest.json", manifest)
    return manifest


def answer(eid="O001", flagged=False):
    value = annotation([segment(0, 20, "a1", "transport")])
    value["episode_id"] = eid
    for group in [value["identity_check"]] + value["segments"]:
        for item in group["evidence"]:
            item["camera"] = "left_wrist"
    if flagged:
        value["segments"][0].update(review_required=True, uncertainty="Result is occluded.")
    return value


def fake_post(url, provider, body, keys):
    if url.endswith("input_tokens"):
        return dict(input_tokens=100)
    eid = json.loads(body["input"][0]["content"][0]["text"].splitlines()[-1])["episode_id"]
    return dict(status="completed", model=body["model"], usage=dict(input_tokens=100, output_tokens=100),
                output=[dict(content=[dict(type="output_text", text=json.dumps(answer(eid)))])])


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "run"
        self.manifest = fixture(self.root)

    def test_sampling_preserves_endpoints_and_cap_at_variable_fps(self):
        for fps in (12, 20, 30):
            frames = pipeline.sampling(1022, fps, 2, 32)
            self.assertEqual((frames[0], frames[-1]), (0, 1021))
            self.assertLessEqual(len(frames), 32)
        self.assertEqual(pipeline.sampling(1, 20, 2, 32), [0])

    def test_native_camera_validation_preserves_original(self):
        value = answer()
        original = copy.deepcopy(value)
        common.validate_annotation(value, self.manifest["episodes"][0])
        self.assertEqual(value, original)
        value["segments"][0]["evidence"][0]["camera"] = "agent"
        with self.assertRaisesRegex(ValueError, "unsupplied"):
            common.validate_annotation(value, self.manifest["episodes"][0])

    def test_unseen_failure_onset_is_rejected(self):
        value = answer()
        value["segments"] = [segment(0, 3, "a1", "transport"), segment(3, 20, "a1", "transport", True)]
        for s in value["segments"]:
            s["evidence"][0]["camera"] = "left_wrist"
        with self.assertRaisesRegex(ValueError, "onset"):
            common.validate_annotation(value, self.manifest["episodes"][0])

    def test_changed_image_and_simulation_repo_are_rejected(self):
        common.verify(self.root)
        path = self.root / self.manifest["episodes"][0]["images"][0]["path"]
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Changed"):
            common.verify(self.root)
        self.manifest["repo"] = "simulation/libero"
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, "OopsieData"):
            common.verify(self.root)

    def test_lab_leakage_is_rejected(self):
        self.manifest["episodes"][1]["lab"] = "lab1"
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, "Lab crosses"):
            common.verify(self.root)

    def test_payload_contains_same_native_evidence_and_no_source_labels(self):
        body = pipeline.payload(self.root, self.manifest, self.manifest["episodes"][0], "astra")
        self.assertEqual(body["model"], "gpt-6-astra")
        content = body["input"][0]["content"]
        self.assertEqual(sum(c["type"] == "input_image" for c in content), 3)
        self.assertIn("left_wrist", json.dumps(content))
        self.assertNotIn("episode_annotations", json.dumps(content))

    def test_uncertain_unicode_target_keeps_exact_values_and_masks(self):
        value = answer(flagged=True)
        value["segments"][0]["what_happened"] = 'Uncertain caf\u00e9 \U0001f916 "release".'
        target, masks = common.target_with_masks(value)
        self.assertEqual(json.loads(target), value)
        self.assertFalse(masks["has_unflagged_segment_targets"])
        span = masks["assistant_excluded_char_ranges"][0]
        self.assertEqual(json.loads(target[span["start"]:span["end"]]), value["segments"][0])

    def collect_sol(self):
        with patch.object(pipeline.transport, "post", side_effect=fake_post), \
             patch.object(pipeline.transport, "credentials", return_value={"openai": "fixture"}):
            return pipeline.collect(self.root, 10, teachers=["sol"])

    def test_collect_export_and_reload_preserve_splits_and_masks(self):
        result = self.collect_sol()
        self.assertEqual(result["validated"], 3)
        self.assertEqual(len(result["pending"]), 3)
        out = self.root.parent / "export"
        pipeline.export(self.root, out)
        for split in ("train", "development", "test"):
            _, _, rows = common.load_export(out, split)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["split"], split)
            self.assertFalse(rows[0]["supervision"]["human_verified"])
        with self.assertRaisesRegex(ValueError, "fresh"):
            pipeline.export(self.root, out)

    def test_existing_attempt_is_never_resent(self):
        self.collect_sol()
        with patch.object(pipeline.transport, "post") as post, \
             patch.object(pipeline.transport, "credentials", return_value={"openai": "fixture"}):
            pipeline.collect(self.root, 10, teachers=["sol"])
            post.assert_not_called()

    def test_budget_stops_before_generation(self):
        with patch.object(pipeline.transport, "post", side_effect=fake_post) as post, \
             patch.object(pipeline.transport, "credentials", return_value={"openai": "fixture"}):
            with self.assertRaisesRegex(ValueError, "budget"):
                pipeline.collect(self.root, 0.000001, teachers=["sol"])
            self.assertEqual(post.call_count, 1)
            self.assertTrue(post.call_args.args[0].endswith("input_tokens"))
        self.assertFalse((self.root / "collection.lock").exists())

    def test_tampered_teacher_annotation_is_rejected(self):
        self.collect_sol()
        path = self.root / "traces/O001_sol/annotation.json"
        value = common.read(path)
        value["segments"][0]["what_happened"] = "Changed output"
        path.write_text(json.dumps(value))
        result = pipeline.validate(self.root)
        self.assertEqual(len(result["invalid"]), 1)
        with self.assertRaisesRegex(ValueError, "invalid"):
            pipeline.export(self.root, self.root.parent / "bad_export")

    def test_interrupted_submission_is_not_retried(self):
        def broken(url, *args):
            if url.endswith("input_tokens"):
                return dict(input_tokens=100)
            raise RuntimeError("Unknown network outcome")
        with patch.object(pipeline.transport, "post", side_effect=broken), \
             patch.object(pipeline.transport, "credentials", return_value={"openai": "fixture"}):
            result = pipeline.collect(self.root, 10, teachers=["sol"])
        self.assertEqual(len(result["invalid"]), 1)
        self.assertEqual(result["validated"], 0)
        self.assertEqual(len(list((self.root / "traces").iterdir())), 1)

    def predictions(self, text=None):
        out = self.root.parent / "predictions"
        out.mkdir()
        common.write(out / "generation.json", dict(split="development", manifest_sha256=common.sha(self.root / "manifest.json")))
        common.write(out / "O002.json", dict(text=text if text is not None else json.dumps(answer("O002")), hit_max=False))
        return out

    def test_scoring_teacher_agreement_and_invalid_predictions(self):
        self.collect_sol()
        predictions = self.predictions("not JSON")
        result = score_oopsie.score(self.root, predictions=predictions)
        self.assertEqual(result["kind"], "teacher_agreement")
        self.assertEqual(result["schema_valid_rate"], 0)
        self.assertEqual(result["episodes"][0]["metrics"]["prediction_coverage"], 0)

    def test_independent_reference_requires_blind_review_provenance(self):
        predictions = self.predictions()
        refs = self.root.parent / "references"
        refs.mkdir()
        common.write(refs / "O002.json", answer("O002"))
        metadata = dict(kind="independent_human", reviewers=["Fixture reviewer"], blind_to_teacher=True,
                        manifest_sha256=common.sha(self.root / "manifest.json"), episodes={
                            "O002": dict(annotation="O002.json", sha256=common.sha(refs / "O002.json"))})
        common.write(refs / "references.json", metadata)
        result = score_oopsie.score(self.root, predictions=predictions, references=refs)
        self.assertEqual(result["kind"], "independent_human_reference")
        self.assertEqual(result["schema_valid_rate"], 1)
        metadata["blind_to_teacher"] = False
        (refs / "references.json").write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, "blind"):
            score_oopsie.score(self.root, predictions=predictions, references=refs)

    def test_export_rejects_reassigned_episode_split(self):
        self.collect_sol()
        out = self.root.parent / "export"
        pipeline.export(self.root, out)
        path = out / "train.jsonl"
        row = json.loads(path.read_text())
        row["split"] = "test"
        path.write_text(json.dumps(row) + "\n")
        receipt = common.read(out / "export.json")
        receipt["files"]["train.jsonl"] = common.sha(path)
        (out / "export.json").write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "Split leakage"):
            common.load_export(out)


if __name__ == "__main__":
    unittest.main()
