"""Semantics and IQL integration checks for the matched reward ablation."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd
import torch

from rewards import apply_rewards, reward_array
from agents import AgentConfig, make_agent
from nets import Normalizer


class TestRewards(unittest.TestCase):
    def test_cumulative_per_step_including_terminal_and_missing(self):
        # progress, failure twice, recovery, neutral, aftermath, missing; terminal success on recovery
        labels = np.array([0, 1, 1, 2, 3, 4, -1])
        base = np.array([0, 0, 0, 1, 0, 0, 0], np.float32)
        np.testing.assert_array_equal(reward_array(base), base)
        np.testing.assert_allclose(reward_array(base, labels, mode="failure"),
                                   [0, -.01, -.01, 1, 0, 0, 0])
        np.testing.assert_allclose(reward_array(base, labels, mode="productive"),
                                   [.01, -.01, -.01, 1.01, 0, 0, 0])
        np.testing.assert_allclose(reward_array(base, labels, mode="productive", success_scale=2,
                                               failure_scale=.2, productive_scale=.3),
                                   [.3, -.2, -.2, 2.3, 0, 0, 0])
        np.testing.assert_array_equal(base, [0, 0, 0, 1, 0, 0, 0])

    def test_invalid_scales_and_labels(self):
        for scale in [-1, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                reward_array([0], failure_scale=scale)
        for labels in [None, [], [9]]:
            with self.assertRaises(ValueError):
                reward_array([0], labels, mode="failure")

    def test_integration_and_guards(self):
        args = SimpleNamespace(algo="iql", data="all", segments=None, dataset="fixture",
                               labels="fixture", reward_mode="productive", reward_success_scale=1,
                               reward_failure_scale=.01, reward_productive_scale=.01)
        data = SimpleNamespace(meta={"obs_spec": "v2"}, device="cpu",
            episodes=pd.DataFrame({"ep_id": [0, 1], "length": [2, 2], "success": [True, False]}),
            ep_id=torch.tensor([0, 0, 1, 1]), frame_index=torch.tensor([0, 1, 0, 1]),
            reward=torch.tensor([0., 1., 0., 0.]), done=torch.tensor([0., 1., 0., 1.]))
        labels = SimpleNamespace(seg_label=np.array([0, 2, 1, -1]),
                                 labelled=np.array([True, True, True, False]), source="fixture",
                                 report=lambda: "fixture labels")
        with patch("labels.load", return_value=labels):
            audit = apply_rewards(args, data)
        np.testing.assert_allclose(data.reward, [.01, 1.01, -.01, 0])
        self.assertEqual(audit["terminal_success_count"], 1)
        cfg = AgentConfig(obs_dim=3, act_dim=2, hidden=8, n_layers=1, n_steps=2)
        agent = make_agent("iql", cfg, Normalizer(np.zeros(3), np.ones(3)), "cpu")
        metrics = agent.update(dict(obs=torch.zeros(4, 3), next_obs=torch.ones(4, 3),
                                    action=torch.zeros(4, 2), reward=data.reward, done=data.done))
        self.assertTrue(all(np.isfinite(v) for v in metrics.values()))
        data.meta["obs_spec"] = "v1"
        with self.assertRaisesRegex(ValueError, "observable"):
            apply_rewards(args, data)
        data.meta["obs_spec"] = "v2"
        with self.assertRaisesRegex(ValueError, "semantics"):
            apply_rewards(args, data)  # rejects already-shaped baseline
        args.segments = "awr"
        with self.assertRaisesRegex(ValueError, "no --segments"):
            apply_rewards(args, data)


if __name__ == "__main__":
    unittest.main()
