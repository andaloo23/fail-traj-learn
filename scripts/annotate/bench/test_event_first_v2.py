"""CPU checks for the event_first_v2 adapter (fake backend, stub episode with telemetry, no model).

Run (WSL): python -m unittest discover -s scripts/annotate/bench -p test_event_first_v2.py
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE / "methods", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import event_first_batched  # noqa: E402
import event_first_v2 as v2  # noqa: E402
from local_segmenter import SYSTEM as CHUNK_SYSTEM  # noqa: E402
from test_event_first_methods import CONTRACT_KEYS, FakeBackend, StubEpisode  # noqa: E402

FI, PR, NE, RE = "failure_inducing", "progress", "neutral", "recovery"


class Ep(StubEpisode):
    """StubEpisode with several held runs, an explicit command schedule, a derived aperture and eef motion ranges.

    held_runs: [(first_held, last_held)]; cmd: [(frame, value)] applied in order from that frame on (default open);
    moving: [(start, end)] frame ranges in which the eef advances 3 mm per frame (3 cm per 10-frame chunk).
    Aperture: 0.04 while open; after a CLOSE switch 0.03 for 3 frames, then 0.02 while held, else 0.0.
    """

    def __init__(self, n_chunks, held_runs=(), cmd=(), moving=(), chunk_len=10):
        super().__init__(n_chunks, held=None, chunk_len=chunk_len)
        self.held_runs = [tuple(r) for r in held_runs]
        n = self.n
        command = np.full(n, -1.0)
        for f, v in cmd:
            command[f:] = v
        self.gripper_cmd = command
        ap = np.full(n, 0.04)
        since = None
        for f in range(n):
            if command[f] > 0:
                since = f if (f == 0 or command[f - 1] <= 0) else since
                ap[f] = 0.02 if self.is_held(f) else (0.03 if f - since < 3 else 0.0)
        self.gripper_aperture = ap
        eef = np.zeros((n, 3))
        for f in range(1, n):
            eef[f] = eef[f - 1]
            if any(s <= f - 1 < e for s, e in moving):
                eef[f, 0] += 0.003
        self.eef_xyz = eef

    def is_held(self, i):
        return any(s <= i <= e for s, e in self.held_runs)


class V2Backend(FakeBackend):
    """FakeBackend with per-chunk chunk-label answers: {chunk: (label, event)} or {chunk: [(label, event), ...]} cycled per sample."""

    def __init__(self, ep, chunk_answers=None, **kw):
        super().__init__(ep, **kw)
        self.chunk_answers = chunk_answers or {}
        self.per_chunk_calls = {}

    def _answer(self, system, content):
        if system != CHUNK_SYSTEM:
            return super()._answer(system, content)
        text = "\n".join(b["text"] for b in content if b["type"] == "text")
        self.chunk_texts.append(text)
        c = int(text.split("TARGET chunk ")[1].split(":")[0])
        i = self.per_chunk_calls.get(c, 0)
        self.per_chunk_calls[c] = i + 1
        answer = self.chunk_answers.get(c, (self.chunk_label, "approach"))
        if isinstance(answer, list):
            answer = answer[i % len(answer)]
        label, event = answer
        return json.dumps({"label": label, "object": "alphabet soup", "observation": "gripper moves toward the can", "event": event})


def run_v2(ep, backend, workdir):
    return v2.run(ep, backend, Path(workdir) / "event_first_v2")


def drop_episode(n_chunks=28):
    # approach 0-59 (moving), grasp 59->60, held 60..124, drop 124->125 with the command still CLOSE, idle tail
    return Ep(n_chunks, held_runs=[(60, 124)], cmd=[(57, 1.0)], moving=[(0, 125)])


class CompletionRuleTests(unittest.TestCase):
    def test_normal_drop_episode_has_no_nulls_and_expected_rules(self):
        ep = drop_episode(28)
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep), tmp)
            result = json.loads((Path(tmp) / "event_first_v2" / "result.json").read_text())
        self.assertEqual([(e["type"], e["last_before"], e["first_after"]) for e in pred["events"]], [("grasp", 59, 60), ("drop", 124, 125)])
        self.assertEqual(pred["held_object"], "alphabet_soup_1")
        self.assertNotIn(None, pred["chunk_labels"])
        self.assertEqual(pred["chunk_labels"][:5], [PR] * 5)                       # approach, moving
        self.assertEqual(pred["completion_rules"][:5], ["7_approach"] * 5)
        self.assertEqual(pred["completion_rules"][5], "6_local")                    # grasp chunk (last_before 59)
        self.assertEqual(pred["chunk_labels"][5:12], [PR] * 7)                      # held, local progress with support 1
        self.assertEqual(pred["chunk_labels"][12], FI)
        self.assertEqual(pred["completion_rules"][12], "1_drop")
        self.assertEqual(pred["chunk_labels"][13:], [NE] * 15)                      # tail
        self.assertEqual(pred["completion_rules"][13:], ["9_tail"] * 15)
        self.assertEqual(pred["decisive_chunk"], 12)
        self.assertEqual(pred["cause"], "grasp")
        self.assertEqual(pred["chunk_q"][12], 1.0)
        self.assertEqual(pred["chunk_q"][0], 0.6)
        self.assertEqual(pred["chunk_q"][6], 1.0)                                   # local support 3/3
        self.assertTrue(all(q > 0 for q in pred["chunk_q"]))
        self.assertEqual(result["evidence"]["completion_rules"], pred["completion_rules"])
        self.assertEqual(result["prediction"]["completion_rules"], pred["completion_rules"])
        self.assertEqual(len(result["evidence"]["cascade_chunk_labels"]), 28)
        self.assertTrue(CONTRACT_KEYS.issubset(pred))

    def test_13_chunk_drop_episode(self):
        ep = drop_episode(13)
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep), tmp)
        self.assertEqual(len(pred["chunk_labels"]), 13)
        self.assertNotIn(None, pred["chunk_labels"])
        self.assertEqual(pred["chunk_labels"], [PR] * 12 + [FI])
        self.assertEqual(pred["decisive_chunk"], 12)
        self.assertEqual(pred["cause"], "grasp")

    def test_close_on_nothing_never_held(self):
        # approach until 70, close on nothing at 70 (fingers closed from 73), never held
        ep = Ep(13, held_runs=[], cmd=[(70, 1.0)], moving=[(0, 70)])
        with tempfile.TemporaryDirectory() as tmp:
            backend = V2Backend(ep)
            pred = run_v2(ep, backend, tmp)
        self.assertEqual(pred["events"], [])
        self.assertIsNone(pred["held_object"])
        self.assertEqual(pred["chunk_labels"][:7], [PR] * 7)
        self.assertEqual(pred["chunk_labels"][7], FI)
        self.assertEqual(pred["completion_rules"][7], "3_close_on_nothing")
        self.assertEqual(pred["chunk_labels"][8:], [NE] * 5)
        self.assertEqual(pred["completion_rules"][8:], ["9_tail"] * 5)
        self.assertEqual(pred["decisive_chunk"], 7)
        self.assertEqual(pred["cause"], "grasp")
        self.assertEqual(backend.generate_calls, 0)  # no identification without held frames

    def test_release_as_last_event_is_failure_inducing_and_decisive(self):
        ep = Ep(28, held_runs=[(60, 124)], cmd=[(57, 1.0), (123, -1.0)], moving=[(0, 125)])
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep), tmp)
        self.assertEqual([e["type"] for e in pred["events"]], ["grasp", "release"])
        self.assertEqual(pred["chunk_labels"][12], FI)
        self.assertEqual(pred["completion_rules"][12], "2_release_last")
        self.assertEqual(pred["decisive_chunk"], 12)
        self.assertEqual(pred["cause"], "manipulation")
        self.assertEqual(pred["chunk_labels"][13:], [NE] * 15)
        self.assertNotIn(None, pred["chunk_labels"])

    def test_regrasp_is_recovery_and_held_at_end_localises_stall(self):
        # grasp 59->60, drop 124->125, open at 140, close again at 157, held 160..279, motion stops at frame 200
        ep = Ep(28, held_runs=[(60, 124), (160, 279)], cmd=[(57, 1.0), (140, -1.0), (157, 1.0)], moving=[(0, 125), (140, 200)])
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep), tmp)
        self.assertEqual([e["type"] for e in pred["events"]], ["grasp", "drop", "grasp"])
        self.assertEqual(pred["chunk_labels"][12], FI)
        self.assertEqual(pred["completion_rules"][12], "1_drop")
        self.assertEqual(pred["completion_rules"][13], "8_between")
        self.assertEqual(pred["chunk_labels"][13], NE)                              # 0.3 cm of motion only
        self.assertEqual((pred["chunk_labels"][14], pred["completion_rules"][14]), (PR, "8_between"))
        self.assertEqual((pred["chunk_labels"][15], pred["completion_rules"][15]), (RE, "4_regrasp"))
        self.assertEqual(pred["chunk_labels"][16:20], [PR] * 4)
        self.assertEqual((pred["chunk_labels"][20], pred["completion_rules"][20]), (FI, "6s_stall_decisive"))
        self.assertEqual(pred["chunk_labels"][21:], [NE] * 7)
        self.assertEqual(pred["completion_rules"][21:], ["6s_stall_tail"] * 7)
        self.assertEqual(pred["decisive_chunk"], 20)
        self.assertEqual(pred["cause"], "manipulation")
        self.assertNotIn(None, pred["chunk_labels"])

    def test_held_at_end_without_long_idle_run_has_null_decisive(self):
        ep = Ep(28, held_runs=[(60, 279)], cmd=[(57, 1.0)], moving=[(0, 260)])  # only 2 idle chunks at the end
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep), tmp)
        self.assertEqual([e["type"] for e in pred["events"]], ["grasp"])
        self.assertIsNone(pred["decisive_chunk"])
        self.assertEqual(pred["cause"], "manipulation")
        self.assertEqual(pred["chunk_labels"][5:26], [PR] * 21)
        self.assertEqual(pred["completion_rules"][26:], ["6i_held_idle"] * 2)
        self.assertEqual(pred["chunk_labels"][26:], [NE] * 2)
        self.assertNotIn(None, pred["chunk_labels"])

    def test_wrong_held_object_makes_approach_failure_inducing(self):
        ep = drop_episode(28)
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep, identify="cream cheese"), tmp)
        self.assertEqual(pred["held_object"], "cream_cheese_1")
        self.assertEqual(pred["chunk_labels"][:5], [FI] * 5)
        self.assertEqual(pred["completion_rules"][:5], ["7_wrong_approach"] * 5)
        self.assertEqual((pred["chunk_labels"][5], pred["completion_rules"][5]), (FI, "W_wrong_grasp"))
        self.assertEqual(pred["chunk_labels"][6:12], [NE] * 6)
        self.assertEqual((pred["chunk_labels"][12], pred["completion_rules"][12]), (FI, "1_drop"))
        self.assertEqual(pred["chunk_labels"][13:], [NE] * 15)
        self.assertEqual(pred["decisive_chunk"], 5)
        self.assertEqual(pred["cause"], "sequencing_semantic")

    def test_never_held_wrong_object_local_event(self):
        ep = Ep(13, held_runs=[], cmd=[], moving=[(0, 80)])
        answers = {4: (FI, "wrong_object"),
                   3: [(PR, "approach"), (NE, "none"), ("uncertain", "none")],   # weak support, moving -> progress
                   9: [(PR, "approach"), (NE, "none"), ("uncertain", "none")]}   # weak support, idle -> neutral
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep, chunk_answers=answers), tmp)
        self.assertEqual(pred["events"], [])
        self.assertEqual((pred["chunk_labels"][4], pred["completion_rules"][4], pred["chunk_q"][4]), (FI, "5_local_specific", 1.0))
        self.assertEqual((pred["chunk_labels"][3], pred["completion_rules"][3], pred["chunk_q"][3]), (PR, "10_motion", 0.6))
        self.assertEqual((pred["chunk_labels"][9], pred["completion_rules"][9]), (NE, "10_motion"))
        self.assertEqual(pred["chunk_labels"][0], PR)
        self.assertEqual(pred["completion_rules"][0], "10_local")
        self.assertEqual(pred["decisive_chunk"], 4)
        self.assertEqual(pred["cause"], "sequencing_semantic")
        self.assertNotIn(None, pred["chunk_labels"])

    def test_never_held_without_events_is_unlocalised(self):
        ep = Ep(13, held_runs=[], cmd=[], moving=[(0, 80)])
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep), tmp)
        self.assertIsNone(pred["decisive_chunk"])
        self.assertIsNone(pred["cause"])
        self.assertEqual(pred["chunk_labels"], [PR] * 13)  # local progress with support 1 is kept (rule 10)

    def test_specific_local_failure_is_kept_on_approach(self):
        ep = drop_episode(28)
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep, chunk_answers={2: (FI, "collision"), 3: (FI, "approach")}), tmp)
        self.assertEqual((pred["chunk_labels"][2], pred["completion_rules"][2], pred["chunk_q"][2]), (FI, "5_local_specific", 1.0))
        self.assertEqual((pred["chunk_labels"][3], pred["completion_rules"][3]), (PR, "7_approach"))  # unspecific FI is not kept

    def test_held_chunk_keeps_strong_local_label_else_progress(self):
        ep = drop_episode(28)
        answers = {8: (RE, "grasp"), 9: (NE, "none"), 10: [(PR, "lift"), (NE, "none"), (RE, "none")]}
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep, chunk_answers=answers), tmp)
        self.assertEqual((pred["chunk_labels"][8], pred["completion_rules"][8]), (RE, "6_local"))
        self.assertEqual((pred["chunk_labels"][9], pred["completion_rules"][9]), (PR, "6_held_default"))
        self.assertEqual((pred["chunk_labels"][10], pred["completion_rules"][10], pred["chunk_q"][10]), (PR, "6_held_default", 0.6))

    def test_success_outcome_skips_completion(self):
        ep = drop_episode(13)
        ep.success = True
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_v2(ep, V2Backend(ep), tmp)
            result = json.loads((Path(tmp) / "event_first_v2" / "result.json").read_text())
        self.assertNotIn("completion_rules", pred)
        self.assertIn("skipped", result["evidence"]["completion"])


class BatchedChunkPassTests(unittest.TestCase):
    def test_generate_many_used_for_chunk_passes_with_k_replicas(self):
        ep = drop_episode(28)
        with tempfile.TemporaryDirectory() as tmp:
            backend = V2Backend(ep)
            pred = run_v2(ep, backend, tmp)
            # 2 scans + 3 refine repeats + 2 chunk passes through generate_many; only identification through generate
            self.assertEqual(backend.generate_many_calls, 2 + 3 + 2)
            self.assertEqual(backend.generate_many_prompts, 57 + 57 + 60 + 2 * 3 * 28)
            self.assertEqual(backend.generate_calls, 4)
            self.assertEqual(pred["n_model_calls"], 7 + 4)
            self.assertEqual(len(backend.chunk_texts), 2 * 3 * 28)
            self.assertEqual(set(backend.per_chunk_calls.values()), {6})
            self.assertTrue(all("wrist close-up identification" in t and "alphabet soup" in t for t in backend.chunk_texts))
            rows = [json.loads(p.read_text()) for p in (Path(tmp) / "event_first_v2" / "chunk_pass0").glob("*.json")]
            self.assertEqual(len(rows), 28)
            self.assertTrue(all(len(r["samples"]) == 3 and r["k"] == 3 and r["sampler"] == "generate_many" and r["seed"] == 7100 for r in rows))
            self.assertTrue(all(r["support"] == 1.0 and r["label"] == PR for r in rows))
            # cache hit: a rerun makes no model call and reproduces the prediction
            again = V2Backend(ep)
            second = run_v2(ep, again, tmp)
            self.assertEqual((again.generate_calls, again.generate_many_calls, second["n_model_calls"]), (0, 0, 0))
            for key in ("held_obs", "events", "held_object", "chunk_labels", "chunk_q", "decisive_chunk", "cause", "completion_rules"):
                self.assertEqual(pred[key], second[key])

    def test_privileged_columns_are_never_read(self):
        ep = drop_episode(13)
        with self.assertRaises(AssertionError):
            ep.col("priv.obj_grasped")
        ep.accessed = []
        with tempfile.TemporaryDirectory() as tmp:
            run_v2(ep, V2Backend(ep), tmp)
        self.assertEqual(ep.accessed, [])
        self.assertTrue(all(0 <= f < ep.n for f in ep.frames_seen))

    def test_config(self):
        cfg = v2.CONFIG
        self.assertEqual(cfg["backend"], "generate_many")
        self.assertEqual(cfg["base"], "event_first_batched")
        self.assertEqual((cfg["chunk"]["sampler"], cfg["chunk"]["batch"], cfg["chunk"]["k"], cfg["chunk"]["temperature"]), ("generate_many", 4, 3, 0.3))
        self.assertEqual((cfg["chunk"]["top_p"], cfg["chunk"]["top_k"]), (0.8, 20))
        self.assertTrue(cfg["chunk"]["held_object_fact"])
        self.assertTrue(cfg["completion"]["assumes_failure"])
        self.assertIn("ep.success", cfg["completion"]["uses_recorded_outcome"])
        self.assertEqual(set(cfg["completion"]["rules"]), set(v2.RULES))
        self.assertEqual([p["seed"] for p in cfg["chunk_passes"]], [7100, 9100])
        self.assertFalse(event_first_batched.CONFIG["chunk"].get("sampler"))  # the base config is not mutated
        self.assertNotIn("completion", event_first_batched.CONFIG)
        json.dumps(cfg)

    def test_helpers(self):
        self.assertEqual(v2.runs_of([0, 1, 1, 0, 1]), [(1, 2), (4, 4)])
        held = v2.held_mask_from_events(20, [{"type": "grasp", "first_after": 5, "last_before": 4}, {"type": "drop", "last_before": 9, "first_after": 10},
                                             {"type": "grasp", "first_after": 15, "last_before": 14}])
        self.assertEqual(held.nonzero()[0].tolist(), list(range(5, 10)) + list(range(15, 20)))
        tele = [{"path_cm": 3.0}] * 10 + [{"path_cm": 0.5}] * 5
        self.assertEqual(v2.trailing_idle_start(tele, 3), 10)
        self.assertIsNone(v2.trailing_idle_start(tele[:12], 3))
        self.assertIsNone(v2.trailing_idle_start(tele, 11))


if __name__ == "__main__":
    unittest.main()
