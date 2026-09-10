"""CPU unit tests for the offline-RL pipeline: run with scripts/rl/run_tests.sh."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import labels as L  # noqa: E402
from agents import AgentConfig, SegmentHooks, expectile_loss, make_agent  # noqa: E402
from eval_critic import auc  # noqa: E402
from nets import Normalizer, TanhGaussianActor  # noqa: E402
from obs import OBS_DIM, ObsBuilder, ObsBuilderV2, obs_v2_dim, quat_xyzw_to_rot6d  # noqa: E402
from replay import OfflineData  # noqa: E402
from segments import SegmentSupervision  # noqa: E402


class TestGoalResolution(unittest.TestCase):
    def test_in_predicate_strips_the_region_suffix(self):
        slots = ["alphabet_soup_1", "basket_1", "milk_1"]
        goal = [["in", "alphabet_soup_1", "basket_1_contain_region"]]
        self.assertEqual(C.resolve_goal_slots(slots, goal), (0, 1))

    def test_unary_predicate_has_no_receptacle(self):
        slots = ["wooden_cabinet_1", "bowl_1"]
        self.assertEqual(C.resolve_goal_slots(slots, [["open", "wooden_cabinet_1_top_region"]]), (0, -1))

    def test_falls_back_to_target_objects(self):
        slots = ["ketchup_1", "basket_1"]
        self.assertEqual(C.resolve_goal_slots(slots, [], ["ketchup_1", "basket_1"]), (0, 1))

    def test_unknown_goal_is_not_an_exception(self):
        self.assertEqual(C.resolve_goal_slots(["a_1"], [["in", "zzz", "qqq"]], []), (0, -1))

    def test_family_and_task_id(self):
        self.assertEqual(C.family_of("full_shift12__t7"), "full_shift12")
        self.assertEqual(C.task_id_of("full_shift12__t7"), 7)

    def test_every_init_protocol_family_has_a_corpus_entry(self):
        listed = {f for fams in C.CORPUS.values() for f in fams}
        self.assertTrue(listed <= set(C.INIT_PROTOCOL), listed - set(C.INIT_PROTOCOL))


class TestRot6d(unittest.TestCase):
    def test_identity_quaternion_gives_identity_columns(self):
        r = quat_xyzw_to_rot6d(np.array([[0.0, 0, 0, 1]]))
        np.testing.assert_allclose(r[0], [1, 0, 0, 0, 1, 0], atol=1e-6)

    def test_sign_flip_is_the_same_rotation(self):
        q = np.array([[0.2, -0.4, 0.1, 0.885]], np.float32)
        np.testing.assert_allclose(quat_xyzw_to_rot6d(q), quat_xyzw_to_rot6d(-q), atol=1e-5)

    def test_columns_are_orthonormal(self):
        rng = np.random.default_rng(0)
        q = rng.normal(size=(16, 4)).astype(np.float32)
        r = quat_xyzw_to_rot6d(q).reshape(16, 2, 3)
        np.testing.assert_allclose(np.linalg.norm(r, axis=2), 1.0, atol=1e-5)
        np.testing.assert_allclose((r[:, 0] * r[:, 1]).sum(1), 0.0, atol=1e-5)


def fake_columns(n_frames: int, n_slots: int = 12, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    quats = rng.normal(size=(n_frames, n_slots, 4)).astype(np.float32)
    quats /= np.linalg.norm(quats, axis=2, keepdims=True)
    valid = np.zeros((n_frames, n_slots), np.float32)
    valid[:, :4] = 1.0
    return {
        "priv.eef_pos": rng.normal(size=(n_frames, 3)).astype(np.float32),
        "priv.eef_quat": np.tile([0.0, 0, 0, 1], (n_frames, 1)).astype(np.float32),
        "priv.gripper_qpos": rng.normal(size=(n_frames, 2)).astype(np.float32),
        "priv.gripper_qvel": rng.normal(size=(n_frames, 2)).astype(np.float32),
        "priv.joint_pos": rng.normal(size=(n_frames, 7)).astype(np.float32),
        "priv.joint_vel": rng.normal(size=(n_frames, 7)).astype(np.float32),
        "priv.obj_pos": rng.normal(size=(n_frames, n_slots * 3)).astype(np.float32),
        "priv.obj_quat": quats.reshape(n_frames, -1),
        "priv.obj_valid": valid,
        "priv.obj_gripper_contact": (rng.random((n_frames, n_slots)) > 0.8).astype(np.float32),
        "priv.obj_grasped": (rng.random((n_frames, n_slots)) > 0.9).astype(np.float32),
        "priv.obj_support_contact": (rng.random((n_frames, n_slots)) > 0.5).astype(np.float32),
        "priv.n_contacts": rng.integers(0, 9, (n_frames, 1)).astype(np.float32),
        "priv.arm_contacts": np.zeros((n_frames, 1), np.float32),
        "priv.gripper_static_contacts": np.zeros((n_frames, 1), np.float32),
        "priv.fixture_qpos": np.zeros((n_frames, 16), np.float32),
        "priv.fixture_valid": np.zeros((n_frames, 16), np.float32),
    }


class TestObsBuilder(unittest.TestCase):
    def setUp(self):
        self.n = 9
        self.cols = fake_columns(self.n)
        self.b = ObsBuilder(0, 1, max_steps=100)

    def test_width_matches_the_declared_dim(self):
        self.assertEqual(self.b.from_columns(self.cols, self.n).shape, (self.n, OBS_DIM))

    def test_offline_and_online_paths_agree(self):
        """The whole point of ObsBuilder: from_columns and from_priv must be the same function."""
        offline = self.b.from_columns(self.cols, self.n)
        for t in range(self.n):
            frame = {k: np.asarray(v)[t] for k, v in self.cols.items()}
            np.testing.assert_allclose(self.b.from_priv(frame, t), offline[t], rtol=0, atol=1e-6)

    def test_distractor_block_is_invariant_to_slot_permutation(self):
        """Distractors are sorted by distance, so relabelling non-target slots must not move the obs."""
        base = self.b.from_columns(self.cols, self.n)
        perm = [0, 1, 3, 2] + list(range(4, 12))  # swap two distractor slots
        cols = dict(self.cols)
        for key, w in (("priv.obj_pos", 3), ("priv.obj_quat", 4)):
            a = np.asarray(cols[key]).reshape(self.n, 12, w)[:, perm]
            cols[key] = a.reshape(self.n, -1)
        for key in ("priv.obj_valid", "priv.obj_gripper_contact", "priv.obj_grasped",
                    "priv.obj_support_contact"):
            cols[key] = np.asarray(cols[key])[:, perm]
        np.testing.assert_allclose(self.b.from_columns(cols, self.n), base, atol=1e-6)

    def test_missing_receptacle_zeroes_the_goal_block(self):
        o = ObsBuilder(0, -1, max_steps=100).from_columns(self.cols, self.n)
        np.testing.assert_allclose(o[:, 43:57], 0.0)  # goal block: 27 proprio + 16 target

    def test_time_block_is_the_normalised_step(self):
        o = self.b.from_columns(self.cols, self.n, t0=0)
        np.testing.assert_allclose(o[:, -2], np.arange(self.n) / 100.0, atol=1e-6)
        np.testing.assert_allclose(o[:, -1], 1.0 - np.arange(self.n) / 100.0, atol=1e-6)

    def test_nan_input_does_not_leak_into_the_observation(self):
        cols = dict(self.cols)
        cols["priv.obj_pos"] = np.asarray(cols["priv.obj_pos"]).copy()
        cols["priv.obj_pos"][0, 0] = np.nan
        self.assertTrue(np.isfinite(self.b.from_columns(cols, self.n)).all())


class TestExpectile(unittest.TestCase):
    def test_half_expectile_is_symmetric(self):
        d = torch.tensor([-2.0, 2.0])
        a, b = expectile_loss(d, 0.5)
        self.assertAlmostEqual(a.item(), b.item())

    def test_high_expectile_penalises_underestimates_more(self):
        under = expectile_loss(torch.tensor([2.0]), 0.9)  # Q > V
        over = expectile_loss(torch.tensor([-2.0]), 0.9)
        self.assertGreater(under.item(), over.item())

    def test_accepts_a_per_sample_expectile(self):
        d = torch.tensor([2.0, 2.0])
        out = expectile_loss(d, torch.tensor([0.9, 0.1]))
        self.assertGreater(out[0].item(), out[1].item())


class TestActor(unittest.TestCase):
    def test_log_prob_is_finite_at_the_action_box_corners(self):
        actor = TanhGaussianActor(8, 7)
        obs = torch.zeros(4, 8)
        act = torch.ones(4, 7)  # gripper actions sit exactly at +-1
        lp = actor.log_prob(obs, act)
        self.assertTrue(torch.isfinite(lp).all())
        self.assertTrue(torch.isfinite(actor.log_prob(obs, -act)).all())

    def test_actions_stay_inside_the_box(self):
        actor = TanhGaussianActor(8, 7)
        a = actor.act(torch.randn(32, 8), deterministic=False)
        self.assertTrue((a.abs() <= 1.0).all())


class TestObsV2(unittest.TestCase):
    """obs_v2 is the strictly observable spec: proprioception, frozen visual features, task language,
    time. Its defining property is a negative one - no simulator state reaches the policy."""

    def setUp(self):
        self.n, self.vis_dim, self.lang_dim, self.cams = 6, 5, 4, 2
        self.cols = fake_columns(self.n, seed=3)
        self.vis = np.random.default_rng(0).normal(size=(self.n, self.cams, self.vis_dim)).astype(np.float32)
        self.lang = np.arange(self.lang_dim, dtype=np.float32)
        self.b = ObsBuilderV2(max_steps=20, vis_dim=self.vis_dim, lang_dim=self.lang_dim,
                              n_cameras=self.cams)

    def test_width_matches_the_declared_dim(self):
        out = self.b.from_columns(self.cols, self.n, self.vis, self.lang)
        self.assertEqual(out.shape, (self.n, obs_v2_dim(self.vis_dim, self.cams, self.lang_dim)))
        self.assertEqual(out.shape[1], sum(w for _, w in self.b.blocks()))

    def test_offline_and_online_paths_agree(self):
        offline = self.b.from_columns(self.cols, self.n, self.vis, self.lang)
        for t in range(self.n):
            frame = {k: np.asarray(v)[t] for k, v in self.cols.items()}
            online = self.b.from_priv(frame, t, self.vis[t], self.lang)
            np.testing.assert_allclose(online, offline[t], rtol=0, atol=1e-6)

    def test_no_privileged_field_reaches_the_observation(self):
        """Perturb every simulator-only column and the observation must not move by one bit.

        This is the property the whole obs_v2 change exists to establish, so it is asserted rather than
        argued: object poses, grasp and contact flags, distractor geometry and fixture joints are the
        fields a real robot cannot read, and obs_v1 fed all of them to the policy.
        """
        privileged = [k for k in self.cols if k.startswith("priv.obj") or k.startswith("priv.fixture")
                      or k in ("priv.n_contacts", "priv.arm_contacts", "priv.gripper_static_contacts")]
        self.assertGreater(len(privileged), 5, privileged)
        base = self.b.from_columns(self.cols, self.n, self.vis, self.lang)
        rng = np.random.default_rng(7)
        poisoned = dict(self.cols)
        for k in privileged:
            poisoned[k] = rng.normal(size=np.asarray(self.cols[k]).shape).astype(np.float32)
        np.testing.assert_array_equal(self.b.from_columns(poisoned, self.n, self.vis, self.lang), base)

    def test_proprioception_still_reaches_it(self):
        """The mirror of the test above: the observable fields must NOT be inert."""
        for k in ("priv.eef_pos", "priv.joint_pos", "priv.gripper_qpos"):
            bumped = dict(self.cols)
            bumped[k] = np.asarray(self.cols[k], np.float32) + 1.0
            self.assertFalse(np.array_equal(self.b.from_columns(bumped, self.n, self.vis, self.lang),
                                            self.b.from_columns(self.cols, self.n, self.vis, self.lang)),
                             f"{k} does not affect the observation")

    def test_language_is_constant_over_the_episode_and_present(self):
        out = self.b.from_columns(self.cols, self.n, self.vis, self.lang)
        start = 27 + self.cams * self.vis_dim
        block = out[:, start:start + self.lang_dim]
        np.testing.assert_allclose(block, np.broadcast_to(self.lang, block.shape))
        other = self.b.from_columns(self.cols, self.n, self.vis, self.lang + 1.0)
        self.assertFalse(np.array_equal(out, other), "the instruction does not reach the observation")

    def test_a_wrong_sized_embedding_is_rejected(self):
        with self.assertRaises(AssertionError):
            self.b.from_columns(self.cols, self.n, self.vis, np.zeros(self.lang_dim + 1, np.float32))


def fake_batch(n=64, obs_dim=12, act_dim=7, device="cpu"):
    g = torch.Generator().manual_seed(0)
    return {
        "obs": torch.randn(n, obs_dim, generator=g), "next_obs": torch.randn(n, obs_dim, generator=g),
        "action": torch.rand(n, act_dim, generator=g) * 2 - 1,
        "reward": (torch.rand(n, generator=g) > 0.9).float(),
        "done": (torch.rand(n, generator=g) > 0.9).float(),
        "success": (torch.rand(n, generator=g) > 0.5).float(),
        "idx": torch.arange(n),
    }


class TestAgents(unittest.TestCase):
    def setUp(self):
        self.obs_dim, self.act_dim = 12, 7
        self.norm = Normalizer(np.zeros(self.obs_dim, np.float32), np.ones(self.obs_dim, np.float32))
        self.cfg = AgentConfig(obs_dim=self.obs_dim, act_dim=self.act_dim, hidden=32, n_layers=2, n_steps=10)

    def test_bc_update_produces_finite_metrics(self):
        agent = make_agent("bc", self.cfg, self.norm, "cpu")
        m = agent.update(fake_batch(obs_dim=self.obs_dim))
        self.assertTrue(all(np.isfinite(v) for v in m.values()), m)

    def test_iql_update_produces_finite_metrics(self):
        agent = make_agent("iql", self.cfg, self.norm, "cpu")
        for _ in range(3):
            m = agent.update(fake_batch(obs_dim=self.obs_dim))
        self.assertTrue(all(np.isfinite(v) for v in m.values()), m)

    def test_outcome_weighting_downweights_failures(self):
        cfg = AgentConfig(**{**self.cfg.__dict__, "bc_weight_mode": "outcome", "bc_failure_weight": 0.1})
        agent = make_agent("bc", cfg, self.norm, "cpu")
        b = fake_batch(obs_dim=self.obs_dim)
        w = agent.weights(b)
        self.assertTrue(torch.allclose(w[b["success"] > 0.5], torch.tensor(1.0)))
        self.assertTrue(torch.allclose(w[b["success"] < 0.5], torch.tensor(0.1)))

    def test_default_hooks_leave_the_baseline_unchanged(self):
        h = SegmentHooks()
        b = fake_batch(obs_dim=self.obs_dim)
        self.assertIs(h.reward(b, b["reward"]), b["reward"])
        self.assertIs(h.done(b, b["done"]), b["done"])
        self.assertEqual(h.expectile(b, 0.7), 0.7)
        self.assertEqual(h.critic_loss(b, torch.zeros(64)), (None, {}))

    def test_checkpoint_round_trip_reproduces_actions(self):
        agent = make_agent("iql", self.cfg, self.norm, "cpu")
        agent.update(fake_batch(obs_dim=self.obs_dim))
        obs = torch.randn(5, self.obs_dim)
        before = agent.act(obs)
        clone = make_agent("iql", self.cfg, self.norm, "cpu")
        clone.load_state_dict(agent.state_dict())
        torch.testing.assert_close(before, clone.act(obs))


def seg_labels(n: int, **columns) -> L.SegmentLabels:
    """A SegmentLabels with every column defaulted, so a test names only the ones it is about."""
    base = dict(
        seg_label=np.zeros(n, np.int8), q=np.ones(n, np.float32), chunk=np.zeros(n, np.int32),
        decisive=np.full(n, -1, np.int32), onset=np.full(n, -1, np.int32),
        cause=np.full(n, -1, np.int8), event=np.zeros(n, np.int8), held=np.zeros(n, bool),
        source="test", coverage={}, event_at=np.zeros(n, np.int8), event_target=np.zeros(n, bool),
        event_hold=np.full(n, -1, np.int32), event_missed=np.zeros(n, bool))
    base.update(columns)
    return L.SegmentLabels(**base)


class TestSegmentLabelSemantics(unittest.TestCase):
    def test_sign_mapping_matches_the_proposal(self):
        sl = L.SegmentLabels(
            seg_label=np.array([0, 1, 2, 3, 4, -1], np.int8), q=np.ones(6, np.float32),
            chunk=np.zeros(6, np.int32), decisive=np.full(6, -1, np.int32),
            onset=np.full(6, -1, np.int32), cause=np.full(6, -1, np.int8),
            event=np.zeros(6, np.int8), held=np.zeros(6, bool), source="test", coverage={})
        np.testing.assert_array_equal(sl.sign, [1, -1, 1, 0, 0, 0])
        np.testing.assert_array_equal(sl.labelled, [True] * 5 + [False])

    def test_rho_peaks_at_the_decisive_chunk_and_decays(self):
        sl = L.SegmentLabels(
            seg_label=np.zeros(4, np.int8), q=np.ones(4, np.float32),
            chunk=np.array([3, 4, 5, 9], np.int32), decisive=np.full(4, 5, np.int32),
            onset=np.full(4, -1, np.int32), cause=np.full(4, -1, np.int8),
            event=np.zeros(4, np.int8), held=np.zeros(4, bool), source="test", coverage={})
        r = sl.rho(2.0)
        self.assertAlmostEqual(r[2], 1.0, places=6)
        self.assertTrue(r[0] < r[1] < r[2])
        self.assertLess(r[3], r[0])

    def test_rho_is_one_without_a_decisive_chunk_or_kappa(self):
        sl = L.SegmentLabels(
            seg_label=np.zeros(3, np.int8), q=np.ones(3, np.float32), chunk=np.arange(3, dtype=np.int32),
            decisive=np.full(3, -1, np.int32), onset=np.full(3, -1, np.int32),
            cause=np.full(3, -1, np.int8), event=np.zeros(3, np.int8), held=np.zeros(3, bool),
            source="test", coverage={})
        np.testing.assert_array_equal(sl.rho(2.0), np.ones(3))
        np.testing.assert_array_equal(sl.rho(0.0), np.ones(3))

    def test_event_columns_are_optional_on_an_old_export(self):
        sl = L.SegmentLabels(
            seg_label=np.zeros(2, np.int8), q=np.ones(2, np.float32), chunk=np.zeros(2, np.int32),
            decisive=np.full(2, -1, np.int32), onset=np.full(2, -1, np.int32),
            cause=np.full(2, -1, np.int8), event=np.zeros(2, np.int8), held=np.zeros(2, bool),
            source="test", coverage={})
        self.assertFalse(sl.has_event_frames)
        self.assertTrue(seg_labels(2).has_event_frames)

    def test_label_vocabulary_matches_the_oracle_reference(self):
        """Read the oracle tuple from source rather than importing it: `annotate/bench` has its own
        `common` module, which would shadow ours on sys.path."""
        src = (Path(__file__).resolve().parents[1] / "annotate" / "bench" / "oracle_reference.py").read_text()
        line = next(ln for ln in src.splitlines() if ln.startswith("LABELS = "))
        oracle = eval(line.split("=", 1)[1].strip())  # noqa: S307 - a literal tuple in our own repo
        self.assertEqual(set(L.LABELS), set(oracle))


class TestAuc(unittest.TestCase):
    """Ties are the case the first implementation got wrong, and a collapsed critic is all ties."""

    def test_a_constant_score_is_uninformative(self):
        self.assertAlmostEqual(auc(np.ones(4), np.array([True, False, True, False])), 0.5)

    def test_perfect_and_inverted_separation(self):
        y = np.array([True, True, False, False])
        self.assertAlmostEqual(auc(np.array([1.0, 2.0, -1.0, -2.0]), y), 1.0)
        self.assertAlmostEqual(auc(np.array([-1.0, -2.0, 1.0, 2.0]), y), 0.0)

    def test_one_tied_pair_counts_half(self):
        # positives {1, 0}, negatives {0, -1}: 1 beats both, the two zeros tie -> (2 + 0.5 + 1) / 4
        y = np.array([True, True, False, False])
        self.assertAlmostEqual(auc(np.array([1.0, 0.0, 0.0, -1.0]), y), 0.875)

    def test_matches_the_pairwise_definition_under_heavy_ties(self):
        rng = np.random.default_rng(0)
        for _ in range(20):
            scores = rng.integers(0, 3, size=40).astype(float)  # only 3 distinct values: ties everywhere
            y = rng.random(40) > 0.5
            pos, neg = scores[y], scores[~y]
            pairwise = ((pos[:, None] > neg) + 0.5 * (pos[:, None] == neg)).mean()
            self.assertAlmostEqual(auc(scores, y), float(pairwise), places=10)


class TestEventReward(unittest.TestCase):
    """Regression tests for docs/rl_verification.md finding 1: the reward has to land on the event's own
    frame, pay out for grasps, and only charge releases that actually missed."""

    def labels(self):
        n = 7
        at = np.zeros(n, np.int8)
        at[1] = L.EVENT_IDX["grasp"]    # target grasp, hold lasts -> +1
        at[2] = L.EVENT_IDX["grasp"]    # target grasp, slips after 3 frames -> nothing
        at[3] = L.EVENT_IDX["grasp"]    # a distractor grasp -> nothing
        at[4] = L.EVENT_IDX["drop"]     # target drop -> -1
        at[5] = L.EVENT_IDX["release"]  # release that left the target away from the goal -> -0.5
        at[6] = L.EVENT_IDX["release"]  # the placement that completed the task -> nothing
        return seg_labels(
            n, event_at=at,
            event_target=np.array([False, True, True, False, True, True, True]),
            event_hold=np.array([-1, 20, 3, 20, 20, 20, 20], np.int32),
            event_missed=np.array([False, False, False, False, False, True, False]))

    def test_reward_lands_on_the_event_frame_with_the_right_sign(self):
        r = SegmentSupervision._event_reward(self.labels())
        np.testing.assert_allclose(r, [0.0, 1.0, 0.0, 0.0, -1.0, -0.5, 0.0])

    def test_grasps_are_actually_rewarded(self):
        self.assertGreater((SegmentSupervision._event_reward(self.labels()) > 0).sum(), 0)

    def test_a_successful_placement_is_not_penalised(self):
        r = SegmentSupervision._event_reward(self.labels())
        self.assertEqual(r[6], 0.0)

    def test_an_export_without_timestamps_is_refused_not_silently_empty(self):
        sl = seg_labels(3)
        sl.event_at = None
        with self.assertRaises(SystemExit):
            SegmentSupervision._event_reward(sl)


class TestPotentialShaping(unittest.TestCase):
    """The `potential` mode is the control for "is the gain just faster credit assignment?", so its one
    job is to leave every episode's discounted return untouched."""

    def setup_two_episodes(self):
        # episode A: 5 frames, episode B: 4 frames; budget 10 steps each
        fidx = np.array([0, 1, 2, 3, 4, 0, 1, 2, 3], np.int32)
        done = np.array([0, 0, 0, 0, 1, 0, 0, 0, 1], bool)
        labels = np.array([0, 0, 1, 2, 4, 3, 0, 0, 1], np.int8)  # progress/failure/recovery/neutral/after
        sl = seg_labels(len(fidx), seg_label=labels)
        return sl, fidx, done, np.full(len(fidx), 10.0, np.float32)

    def test_the_initial_potential_is_zero(self):
        sl, fidx, done, horizon = self.setup_two_episodes()
        phi, _ = SegmentSupervision._potential(sl, fidx, done, horizon)
        np.testing.assert_array_equal(phi[fidx == 0], [0.0, 0.0])

    def test_the_shaped_return_of_every_episode_is_zero(self):
        sl, fidx, done, horizon = self.setup_two_episodes()
        phi, phi_next = SegmentSupervision._potential(sl, fidx, done, horizon)
        gamma = 0.995
        shaped = gamma * phi_next - phi
        for start in np.flatnonzero(fidx == 0):
            end = start + int(np.flatnonzero(done[start:])[0]) + 1
            total = np.sum(gamma ** fidx[start:end] * shaped[start:end])
            self.assertAlmostEqual(float(total), 0.0, places=6)

    def test_the_potential_does_not_depend_on_the_realised_length(self):
        """Two episodes with the same prefix and the same budget get the same Phi on that prefix, even
        though one runs longer. Dividing by the realised length made them differ."""
        sl, fidx, done, horizon = self.setup_two_episodes()
        phi, _ = SegmentSupervision._potential(sl, fidx, done, horizon)
        short = seg_labels(4, seg_label=sl.seg_label[:4])
        phi_short, _ = SegmentSupervision._potential(
            short, fidx[:4], np.array([0, 0, 0, 1], bool), horizon[:4])
        np.testing.assert_allclose(phi[:4], phi_short)


class TestNormalisationSplit(unittest.TestCase):
    """docs/rl_verification.md finding 5: whitening was fit on the whole corpus, validation included."""

    def build_dataset_dir(self, root: Path):
        n_ep, per_ep, obs_dim, act_dim = 20, 6, 4, 3
        n = n_ep * per_ep
        rng = np.random.default_rng(0)
        ep_id = np.repeat(np.arange(n_ep), per_ep).astype(np.int32)
        obs = (rng.normal(size=(n, obs_dim)) + ep_id[:, None] * 3.0).astype(np.float32)
        done = np.zeros(n, bool)
        done[per_ep - 1::per_ep] = True
        arrays = {
            "obs": obs, "next_obs": obs.copy(),
            "action": rng.uniform(-1, 1, size=(n, act_dim)).astype(np.float32),
            "reward": np.zeros(n, np.float32), "done": done, "timeout": done,
            "ep_id": ep_id, "frame_index": np.tile(np.arange(per_ep), n_ep).astype(np.int32),
        }
        for k, v in arrays.items():
            np.save(root / f"{k}.npy", v)
        pd.DataFrame({"ep_id": np.arange(n_ep), "success": np.arange(n_ep) % 2 == 0,
                      "length": per_ep, "max_steps": 10}).to_parquet(root / "episodes.parquet")
        (root / "meta.json").write_text(json.dumps({
            "spec_version": "obs_v1", "obs_dim": obs_dim, "action_dim": act_dim,
            "obs_mean": obs.mean(0).tolist(), "obs_std": obs.std(0).tolist()}))
        return obs

    def test_whitening_uses_only_the_training_episodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            obs = self.build_dataset_dir(root)
            data = OfflineData(root, device="cpu", val_frac=0.2, seed=0)
            train = data.train_idx.numpy()
            np.testing.assert_allclose(data.norm_mean, obs[train].mean(0), rtol=1e-5, atol=1e-5)
            # The episodes are offset from each other, so holding some out really does move the mean:
            # if this ever stops being true the test has stopped testing anything.
            self.assertGreater(np.abs(data.norm_mean - obs.mean(0)).max(), 1e-3)
            np.testing.assert_allclose(data.obs_mean, obs.mean(0), rtol=1e-5, atol=1e-5)


if __name__ == "__main__":
    unittest.main()
