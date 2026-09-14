"""CPU regression tests; synthetic fixtures do not establish physical causality."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from failure_data import FailureCorpus, FailureWindows
from failure_nets import FailureConfig, FailureModel, failure_loss, model_inputs
from train_failure_model import binary_metrics


def fixture(root):
    data = root / "data"
    data.mkdir()
    lengths = [5, 5, 5]
    np.save(data / "obs.npy", np.concatenate([np.full((n, 3), i*100, np.float32) for i, n in enumerate(lengths)]))
    np.save(data / "action.npy", np.arange(30, dtype=np.float32).reshape(15, 2)/30)
    np.save(data / "ep_id.npy", np.repeat(np.arange(3), lengths))
    np.save(data / "frame_index.npy", np.tile(np.arange(5), 3))
    (data / "meta.json").write_text(json.dumps(dict(spec_version="obs_v2")))
    pd.DataFrame([dict(dataset="source", episode_index=i, ep_id=i) for i in range(3)]).to_parquet(data / "episodes.parquet")
    episodes = []
    for i, split in enumerate(("train", "val", "test")):
        episodes.append(dict(dataset="source", episode_index=i, split=split, split_group=f"episode-{i}",
            provenance="synthetic unit-test labels", fps=10,
            segments=[dict(start_chunk=0, end_chunk_exclusive=1, role="progress"),
                      dict(start_chunk=1, end_chunk_exclusive=3, role="failure_inducing", failure_types=["grasp"])],
            category_coverage=[dict(start_chunk=0, end_chunk_exclusive=3, classes=["grasp"])],
            event_coverage=[dict(start_frame=0, end_frame_exclusive=5, classes=["drop"])],
            events=[dict(type="drop", frame=4, seconds=.4)]))
    manifest = dict(version=1, chunk_size=2, categories=["grasp", "collision"], event_types=["drop"], episodes=episodes)
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest))
    return data, path, manifest


class DataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data, self.path, self.manifest = fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def load(self):
        self.path.write_text(json.dumps(self.manifest))
        return FailureCorpus(self.data, self.path)

    def test_alignment_unknown_and_partial_chunk(self):
        c = self.load()
        b = FailureWindows(c, "train", 4)[0]
        np.testing.assert_array_equal(c.mean, np.zeros(3))  # excludes val/test
        np.testing.assert_array_equal(b["category"][:, 0], [0, 1, 1, -1])
        np.testing.assert_array_equal(b["category"][:, 1], [-1]*4)
        np.testing.assert_array_equal(b["event"][:, 0], [0, 0, 1, -1])
        np.testing.assert_allclose(b["duration"][:, 0], [.2, .2, .1, 0])
        np.testing.assert_array_equal(b["action_valid"][2], [True, False])
        np.testing.assert_allclose(b["action"][1], c.actions[2:4])
        # Only the pre-chunk observation is read.
        obs = np.load(self.data / "obs.npy")
        obs[1] = 999
        np.save(self.data / "obs.npy", obs)
        after = FailureWindows(self.load(), "train", 4)[0]
        torch.testing.assert_close(b["obs"], after["obs"])

    def test_window_targets_do_not_copy_episode_outcome(self):
        c = self.load()
        ds = FailureWindows(c, "train", 1)
        self.assertEqual(len(ds), 3)
        self.assertEqual(ds[0]["category"][0, 0], 0)
        self.assertEqual(ds[1]["category"][0, 0], 1)
        self.assertEqual(ds[0]["event"][0, 0], 0)
        self.assertTrue(all(c.episodes[i]["split"] == "train" for i, _, _ in ds.windows))

    def test_unknown_history_prevents_negative_prefix(self):
        self.manifest["episodes"][0]["category_coverage"][0]["start_chunk"] = 1
        b = FailureWindows(self.load(), "train", 4)[0]
        self.assertEqual(b["category"][0, 0], -1)
        self.assertEqual(b["category"][1, 0], 1)

    def test_reject_group_overlap(self):
        self.manifest["episodes"][1]["split_group"] = "episode-0"
        with self.assertRaisesRegex(ValueError, "crosses"):
            self.load()

    def test_reject_duplicate_episode(self):
        self.manifest["episodes"].append(copy.deepcopy(self.manifest["episodes"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.load()

    def test_reject_bad_time(self):
        self.manifest["episodes"][0]["events"][0]["seconds"] = 1.0
        with self.assertRaisesRegex(ValueError, "seconds"):
            self.load()

    def test_reject_privileged(self):
        (self.data / "meta.json").write_text(json.dumps(dict(spec_version="obs_v1")))
        with self.assertRaisesRegex(ValueError, "obs_v2"):
            self.load()

    def test_cli_checkpoint_round_trip(self):
        out = self.root / "run"
        command = [sys.executable, str(Path(__file__).with_name("train_failure_model.py")),
            "--dataset", str(self.data), "--manifest", str(self.path), "--out", str(out),
            "--epochs", "1", "--width", "16", "--heads", "2", "--layers", "1",
            "--max-chunks", "4", "--device", "cpu"]
        import os
        env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
        run = subprocess.run(command, capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        checkpoint = torch.load(out / "best.pt", weights_only=False, map_location="cpu")
        restored = FailureModel(FailureConfig(**checkpoint["config"]))
        restored.load_state_dict(checkpoint["model"])
        self.assertEqual(checkpoint["normalization"]["mean"], [0, 0, 0])
        metrics = json.loads((out / "metrics.jsonl").read_text())
        self.assertTrue(np.isfinite(metrics["val"]["loss"]))
        self.assertEqual(metrics["val"]["category"][1]["known"], 0)


class ModelTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        torch.manual_seed(7)
        self.model = FailureModel(FailureConfig(3, 2, 2, 2, 1, width=16, layers=2,
                                                heads=2, max_chunks=4, dropout=0))
        self.batch = dict(obs=torch.randn(2, 4, 3), action=torch.randn(2, 4, 2, 2),
            action_valid=torch.ones(2, 4, 2, dtype=torch.bool), duration=torch.ones(2, 4, 1),
            valid=torch.ones(2, 4, dtype=torch.bool), role=torch.zeros(2, 4, dtype=torch.long),
            role_weight=torch.ones(2, 4), event=torch.zeros(2, 4, 1), event_weight=torch.ones(2, 4, 1),
            category=torch.zeros(2, 4, 2), category_weight=torch.ones(2, 4, 2))

    def test_causality_including_query_pooling(self):
        self.model.eval()
        before = self.model(**model_inputs(self.batch))
        self.batch["obs"][:, 2:] += 100
        self.batch["action"][:, 2:] *= -100
        after = self.model(**model_inputs(self.batch))
        for name in ("contextual", "role", "event", "category"):
            torch.testing.assert_close(before[name][:, :2], after[name][:, :2])
        future = torch.ones(4, 4, dtype=torch.bool).triu(1)
        self.assertEqual(before["attention"].permute(0, 2, 1, 3)[:, :, future].abs().sum(), 0)

    def test_padding_and_unknown_losses(self):
        self.batch["valid"][:, 2:] = False
        before = self.model(**model_inputs(self.batch))
        l1, _ = failure_loss(before, self.batch)
        self.batch["obs"][:, 2:] = 1000
        self.batch["action"][:, 2:] = -1000
        self.batch["category"][:, 2:] = 1
        self.batch["event"][:, 2:] = 1
        after = self.model(**model_inputs(self.batch))
        l2, _ = failure_loss(after, self.batch)
        torch.testing.assert_close(l1, l2)
        for name in ("role", "event", "category"):
            torch.testing.assert_close(before[name][:, :2], after[name][:, :2])
            self.batch[name].fill_(-1)
        loss, _ = failure_loss(after, self.batch)
        self.assertEqual(float(loss.detach()), 0)
        self.assertTrue(torch.isfinite(loss))

    def test_gradients_reach_encoder_attention_and_heads(self):
        loss, _ = failure_loss(self.model(**model_inputs(self.batch)), self.batch)
        loss.backward()
        for p in (self.model.chunk_encoder[0].weight,
                  self.model.temporal.layers[0].self_attn.in_proj_weight,
                  self.model.queries, self.model.role_head.weight, self.model.event_head.weight,
                  self.model.category_readout):
            self.assertGreater(float(p.grad.abs().sum()), 0)

    def test_learns_synthetic_history_dependency(self):
        # Endpoint labels depend on an earlier observation, with independent endpoint input.
        b = self.batch
        b["obs"][0, 0, 0], b["obs"][1, 0, 0] = -3, 3
        for name in ("category_weight", "role_weight", "event_weight"):
            b[name].zero_()
        b["category_weight"][:, -1, 0] = 1
        b["category"][1, -1, 0] = 1
        optim = torch.optim.Adam(self.model.parameters(), lr=.01)
        initial = float(failure_loss(self.model(**model_inputs(b)), b)[0].detach())
        for _ in range(80):
            optim.zero_grad()
            loss, _ = failure_loss(self.model(**model_inputs(b)), b)
            loss.backward()
            optim.step()
        final = float(failure_loss(self.model(**model_inputs(b)), b)[0].detach())
        self.assertLess(final, initial * .1)

    def test_tied_average_precision(self):
        metrics = binary_metrics(np.zeros((4, 1)), np.array([[1], [0], [1], [0]]), np.ones((4, 1)))
        self.assertAlmostEqual(metrics[0]["average_precision"], .5)


if __name__ == "__main__":
    unittest.main()
