"""CPU-only unit tests for the benchmark scorer, harness helpers and the whole_p8 adapter mapping.

Run inside WSL:  bench.sh test_bench.py     (or python -m unittest bench/test_bench.py)
"""
import copy
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
ANNOTATE_DIR = BENCH_DIR.parent
for _p in (str(ANNOTATE_DIR), str(BENCH_DIR)):
    if _p not in sys.path:
        sys.path.append(_p)

import score  # noqa: E402
from methods import REGISTRY, load_method  # noqa: E402
from methods.whole_p8 import CONFIG, build_args, record_to_prediction  # noqa: E402
from score import LEVELS, aggregate_method, render_markdown, score_episode, score_methods  # noqa: E402


# ------------------------------------------------------------------ synthetic data
def make_reference(**over):
    """drop_transport episode, 6 chunks of 10 frames; held bowl_1 frames 20..39 (ambiguous fringes), drop in chunk 4."""
    ref = {
        "reference_version": "r2", "dataset": "ds", "episode_index": 7, "suite": "s", "task_id": 1, "task": "t",
        "success": False, "n_frames": 60, "fps": 20, "n_chunks": 6, "chunks": [[0, 10], [10, 20], [20, 30], [30, 40], [40, 50], [50, 60]],
        "object_slots": ["bowl_1", "plate_1"], "target_slot": "bowl_1", "goal_slot": "plate_1", "fixtures": [],
        "held_runs": [
            {"start": 0, "end": 17, "state": "empty", "object": None},
            {"start": 18, "end": 19, "state": "ambiguous", "object": None},
            {"start": 20, "end": 39, "state": "held", "object": "bowl_1"},
            {"start": 40, "end": 41, "state": "ambiguous", "object": None},
            {"start": 42, "end": 59, "state": "empty", "object": None},
        ],
        "events": [
            {"index": 20, "type": "grasp", "object": "bowl_1", "last_before": 19, "first_after": 20, "chunk": 2, "gripper_cmd_open": False},
            {"index": 40, "type": "drop", "object": "bowl_1", "last_before": 39, "first_after": 40, "chunk": 4, "gripper_cmd_open": False},
        ],
        "wrong_object_contacts": [], "collisions": [], "fixture_motion": [],
        "stage_frames": {"reached": 15, "grasped": 20, "lifted": 25, "transported": 30, "placed": -1},
        "final": {"target_in_goal": False, "target_resting": True, "target_dist_to_goal_xy_m": 0.1, "target_z_m": 0.9, "target_moved_m": 0.2},
        "failure_mode": "drop_transport", "cause": "grasp", "decisive_chunk": 4,
        "chunk_labels": [
            {"chunk": 0, "allowed": ["progress"], "primary": "progress", "rule": "pre_advance"},
            {"chunk": 1, "allowed": ["progress", "neutral"], "primary": "progress", "rule": "pre_other"},
            {"chunk": 2, "allowed": ["progress"], "primary": "progress", "rule": "pre_advance"},
            {"chunk": 3, "allowed": ["progress"], "primary": "progress", "rule": "pre_advance"},
            {"chunk": 4, "allowed": ["failure_inducing"], "primary": "failure_inducing", "rule": "decisive"},
            {"chunk": 5, "allowed": ["aftermath", "neutral"], "primary": "aftermath", "rule": "post"},
        ],
    }
    ref.update(over)
    return ref


def make_prediction(**over):
    pred = {
        "method": "m", "method_config": {}, "dataset": "ds", "episode_index": 7,
        "held_obs": [{"frame": 5, "state": "empty", "object": None}, {"frame": 19, "state": "held", "object": "bowl_1"},  # 19 ambiguous -> ignored
                     {"frame": 30, "state": "held", "object": "bowl_1"}, {"frame": 50, "state": "empty", "object": None}],
        "events": [{"type": "grasp", "object": "bowl_1", "last_before": 21, "first_after": 22},
                   {"type": "drop", "object": "bowl_1", "last_before": 38, "first_after": 41}],
        "held_object": "bowl_1",
        "chunk_labels": ["progress", "neutral", "progress", "progress", "failure_inducing", "aftermath"],
        "chunk_q": [1.0, 0.8, 1.0, 1.0, 0.6, 1.0],
        "decisive_chunk": 5, "cause": "grasp",
        "n_model_calls": 3, "wall_s": 12.5, "peak_mem_gb": 18.2, "raw_dir": "/x",
    }
    pred.update(over)
    return pred


def status(ref, pred, level):
    return score_episode(ref, pred)["levels"][level]["status"]


# ------------------------------------------------------------------ tests
class LevelTests(unittest.TestCase):
    def test_all_pass(self):
        res = score_episode(make_reference(), make_prediction())
        self.assertTrue(res["pass"], res)
        self.assertIsNone(res["first_fail"])
        for lv in LEVELS:
            self.assertEqual(res["levels"][lv]["status"], "pass", (lv, res["levels"][lv]))

    # held_state (diagnostic since r2: reported, never fails the episode)
    def test_held_state_uncertain_counts_as_wrong_but_is_diagnostic(self):
        pred = make_prediction()
        pred["held_obs"][2]["state"] = "uncertain"
        res = score_episode(make_reference(), pred)
        self.assertEqual(res["levels"]["held_state"]["status"], "fail")
        self.assertTrue(res["pass"]); self.assertIsNone(res["first_fail"])
        self.assertAlmostEqual(res["levels"]["held_state"]["accuracy"], 2 / 3)
        self.assertIn("frame 30", res["levels"]["held_state"]["detail"])

    def test_level_sets(self):
        self.assertEqual(score.OVERALL_LEVELS, ["events", "held_object", "chunk_labels", "decisive", "cause"])
        self.assertEqual(set(score.DIAGNOSTIC_LEVELS), {"held_state", "chunk_labels_1off"})
        self.assertEqual(set(LEVELS), set(score.OVERALL_LEVELS) | set(score.DIAGNOSTIC_LEVELS))
        self.assertEqual(set(score.LEVEL_FN), set(LEVELS))

    def test_held_state_ignores_ambiguous_frames(self):
        pred = make_prediction(held_obs=[{"frame": 18, "state": "held", "object": None}, {"frame": 41, "state": "uncertain", "object": None}])
        self.assertEqual(status(make_reference(), pred, "held_state"), "pass")

    def test_held_state_skipped_when_nothing_judged(self):
        res = score_episode(make_reference(), make_prediction(held_obs=[]))
        self.assertEqual(res["levels"]["held_state"]["status"], "skip")
        self.assertTrue(res["pass"])

    # events (chunk granularity since r2)
    def test_events_tolerance_edges(self):
        ref = make_reference()
        # ref drop: chunk 4 (last_before 39). A predicted drop matches when chunk(pred.last_before) is 3, 4 or 5.
        for lb, want in [(30, "pass"), (39, "pass"), (40, "pass"), (59, "pass"), (29, "fail"), (20, "fail")]:
            p = make_prediction()
            p["events"][1] = {"type": "drop", "object": "bowl_1", "last_before": lb, "first_after": lb + 1}
            self.assertEqual(status(ref, p, "events"), want, lb)
        # only last_before matters, not the bracket length
        wide = make_prediction()
        wide["events"][1] = {"type": "drop", "object": "bowl_1", "last_before": 31, "first_after": 58}
        self.assertEqual(status(ref, wide, "events"), "pass")
        # out-of-range frames clamp to the first/last chunk (like the oracle's chunk lookup)
        far = make_prediction()
        far["events"][1] = {"type": "drop", "object": "bowl_1", "last_before": 120, "first_after": 121}
        self.assertEqual(status(ref, far, "events"), "pass")  # clamps to chunk 5
        far["events"][0] = {"type": "grasp", "object": "bowl_1", "last_before": -5, "first_after": -4}
        res = score_episode(ref, far)
        self.assertEqual(res["levels"]["events"]["status"], "fail")  # chunk 0 vs ref chunk 2
        self.assertIn("ref grasp chunk 2", res["levels"]["events"]["detail"])

    def test_events_chunk_from_reference_chunks_and_ref_chunk_field(self):
        ref = make_reference()
        for e in ref["events"]:
            del e["chunk"]  # falls back to the chunk of ref.last_before
        self.assertEqual(status(ref, make_prediction(), "events"), "pass")
        noch = make_reference(chunks=[])
        self.assertEqual(status(noch, make_prediction(), "events"), "fail")  # predicted events cannot be placed

    def test_events_matching_is_maximum_not_greedy(self):
        ref = make_reference()
        ref["events"] = [{"index": 40, "type": "grasp", "object": "bowl_1", "last_before": 39, "first_after": 40, "chunk": 3},
                         {"index": 51, "type": "grasp", "object": "bowl_1", "last_before": 50, "first_after": 51, "chunk": 5}]
        pred = make_prediction(events=[{"type": "grasp", "object": "bowl_1", "last_before": 45, "first_after": 46},   # chunk 4: fits both
                                       {"type": "grasp", "object": "bowl_1", "last_before": 25, "first_after": 26}])  # chunk 2: fits only the first
        self.assertEqual(status(ref, pred, "events"), "pass")

    def test_events_type_must_match(self):
        pred = make_prediction()
        pred["events"][1]["type"] = "release"
        res = score_episode(make_reference(), pred)
        self.assertEqual(res["levels"]["events"]["status"], "fail")
        self.assertIn("ref drop", res["levels"]["events"]["detail"])

    def test_events_unmatched_prediction_fails(self):
        pred = make_prediction()
        pred["events"].append({"type": "grasp", "object": "bowl_1", "last_before": 50, "first_after": 51})
        res = score_episode(make_reference(), pred)
        self.assertEqual(res["levels"]["events"]["status"], "fail")
        self.assertIn("matches nothing", res["levels"]["events"]["detail"])

    def test_events_missing_prediction_fails_and_empty_both_passes(self):
        self.assertEqual(status(make_reference(), make_prediction(events=[]), "events"), "fail")
        self.assertEqual(status(make_reference(events=[]), make_prediction(events=[]), "events"), "pass")
        self.assertEqual(status(make_reference(events=[]), make_prediction(), "events"), "fail")

    def test_events_one_to_one(self):
        pred = make_prediction()
        pred["events"].append(dict(pred["events"][1]))  # duplicate drop -> second one unmatched
        self.assertEqual(status(make_reference(), pred, "events"), "fail")

    # held_object
    def test_held_object(self):
        self.assertEqual(status(make_reference(), make_prediction(held_object="plate_1"), "held_object"), "fail")
        self.assertEqual(status(make_reference(), make_prediction(held_object=None), "held_object"), "fail")
        ref = make_reference(held_runs=[{"start": 0, "end": 59, "state": "empty", "object": None}])
        res = score_episode(ref, make_prediction(held_object=None))
        self.assertEqual(res["levels"]["held_object"]["status"], "skip")

    def test_held_object_uses_longest_run(self):
        ref = make_reference()
        ref["held_runs"] = [{"start": 0, "end": 4, "state": "held", "object": "plate_1"},
                            {"start": 5, "end": 19, "state": "empty", "object": None},
                            {"start": 20, "end": 39, "state": "held", "object": "bowl_1"},
                            {"start": 40, "end": 59, "state": "empty", "object": None}]
        self.assertEqual(status(ref, make_prediction(held_object="bowl_1"), "held_object"), "pass")
        self.assertEqual(status(ref, make_prediction(held_object="plate_1"), "held_object"), "fail")

    # chunk_labels
    def test_chunk_labels_allowed_set_and_abstain(self):
        ref = make_reference()
        pred = make_prediction()
        pred["chunk_labels"][1] = "progress"  # allowed {progress, neutral}
        self.assertEqual(status(ref, pred, "chunk_labels"), "pass")
        pred["chunk_labels"][1] = "aftermath"
        res = score_episode(ref, pred)
        self.assertEqual(res["levels"]["chunk_labels"]["status"], "fail")
        self.assertIn("chunk 1 predicted aftermath, allowed {progress,neutral}", res["levels"]["chunk_labels"]["detail"])
        self.assertAlmostEqual(res["levels"]["chunk_labels"]["accuracy"], 5 / 6)
        pred["chunk_labels"][1] = None
        res = score_episode(ref, pred)
        self.assertEqual(res["levels"]["chunk_labels"]["status"], "fail")
        self.assertIn("abstained", res["levels"]["chunk_labels"]["detail"])

    def test_chunk_labels_short_list_counts_as_abstain(self):
        pred = make_prediction(chunk_labels=["progress"] * 4)
        self.assertEqual(status(make_reference(), pred, "chunk_labels"), "fail")

    # chunk_labels_1off (diagnostic)
    def test_chunk_labels_1off(self):
        ref = make_reference()
        pred = make_prediction()
        self.assertEqual(status(ref, pred, "chunk_labels_1off"), "pass")
        pred["chunk_labels"][1] = "aftermath"  # one wrong: chunk_labels fails, 1off passes, episode fails
        res = score_episode(ref, pred)
        self.assertEqual(res["levels"]["chunk_labels"]["status"], "fail")
        self.assertEqual(res["levels"]["chunk_labels_1off"]["status"], "pass")
        self.assertEqual(res["levels"]["chunk_labels_1off"]["n_wrong"], 1)
        self.assertEqual(res["first_fail"], "chunk_labels")
        pred["chunk_labels"][5] = None  # two wrong (an abstain counts)
        res = score_episode(ref, pred)
        self.assertEqual(res["levels"]["chunk_labels_1off"]["status"], "fail")
        self.assertIn("2/6 scorable chunks wrong", res["levels"]["chunk_labels_1off"]["detail"])
        self.assertEqual(res["first_fail"], "chunk_labels")  # 1off never becomes first_fail
        # a 1off failure alone never fails the episode: make everything else pass with two wrong labels
        ok = make_prediction()
        self.assertTrue(score_episode(ref, ok)["pass"])
        unl = make_reference(decisive_chunk=None)
        for c in unl["chunk_labels"]:
            c["rule"] = "unlocalised"
        self.assertEqual(status(unl, make_prediction(), "chunk_labels_1off"), "skip")

    def test_chunk_labels_skipped_when_unlocalised(self):
        ref = make_reference(failure_mode="never_reached", cause="reaching", decisive_chunk=None, events=[],
                             held_runs=[{"start": 0, "end": 59, "state": "empty", "object": None}])
        for c in ref["chunk_labels"]:
            c["allowed"], c["rule"] = ["failure_inducing", "neutral", "progress"], "unlocalised"
        pred = make_prediction(chunk_labels=[None] * 6, decisive_chunk=None, cause="reaching", events=[], held_object=None,
                               held_obs=[{"frame": 5, "state": "empty", "object": None}])
        res = score_episode(ref, pred)
        self.assertEqual(res["levels"]["chunk_labels"]["status"], "skip")
        self.assertEqual(res["levels"]["decisive"]["status"], "skip")
        self.assertEqual(res["levels"]["held_object"]["status"], "skip")
        self.assertTrue(res["pass"])

    # decisive
    def test_decisive_tolerance(self):
        ref = make_reference()
        for p, want in [(3, "pass"), (4, "pass"), (5, "pass"), (6, "fail"), (2, "fail"), (None, "fail")]:
            self.assertEqual(status(ref, make_prediction(decisive_chunk=p), "decisive"), want, p)
        res = score_episode(ref, make_prediction(decisive_chunk=12))
        self.assertEqual(res["levels"]["decisive"]["detail"], "decisive 12 vs ref 4")

    def test_decisive_skipped_when_reference_null(self):
        res = score_episode(make_reference(decisive_chunk=None), make_prediction(decisive_chunk=None))
        self.assertEqual(res["levels"]["decisive"]["status"], "skip")

    # cause
    def test_cause(self):
        self.assertEqual(status(make_reference(), make_prediction(cause="manipulation"), "cause"), "fail")
        self.assertEqual(status(make_reference(), make_prediction(cause=None), "cause"), "fail")


class EpisodeAggregateTests(unittest.TestCase):
    def test_first_failing_level_in_order(self):
        pred = make_prediction(cause="collision", decisive_chunk=0)
        res = score_episode(make_reference(), pred)
        self.assertFalse(res["pass"])
        self.assertEqual(res["first_fail"], "decisive")
        pred["held_obs"][2]["state"] = "empty"  # a held_state failure is diagnostic: not the first failing level
        res = score_episode(make_reference(), pred)
        self.assertEqual(res["levels"]["held_state"]["status"], "fail")
        self.assertEqual(res["first_fail"], "decisive")
        pred["events"] = []
        res = score_episode(make_reference(), pred)
        self.assertEqual(res["first_fail"], "events")

    def test_missing_prediction(self):
        res = score_episode(make_reference(), None)
        self.assertFalse(res["pass"])
        self.assertEqual(res["first_fail"], "missing")
        self.assertEqual(res["levels"]["cause"]["status"], "fail")
        self.assertEqual(res["levels"]["events"]["status"], "fail")
        self.assertEqual(res["levels"]["chunk_labels_1off"]["status"], "fail")
        ref = make_reference(decisive_chunk=None)
        self.assertEqual(score_episode(ref, None)["levels"]["decisive"]["status"], "skip")

    def test_error_prediction_fails(self):
        pred = {"error": "RuntimeError: boom", "held_obs": [], "events": [], "held_object": None, "chunk_labels": [None] * 6,
                "chunk_q": [0.0] * 6, "decisive_chunk": None, "cause": None}
        res = score_episode(make_reference(), pred)
        self.assertFalse(res["pass"])
        self.assertEqual(res["first_fail"], "error")

    def test_aggregate_and_markdown(self):
        rows = []
        for i, (ok, mode) in enumerate([(True, "drop_transport"), (False, "drop_transport"), (True, "release_miss")]):
            pred = make_prediction() if ok else make_prediction(cause="other")
            res = score_episode(make_reference(), pred)
            rows.append({"dataset": "ds", "episode_index": i, "failure_mode": mode, "pass": res["pass"], "first_fail": res["first_fail"],
                         "detail": res["detail"], "levels": res["levels"], "n_model_calls": 3, "wall_s": 10.0})
        s = aggregate_method(rows)
        self.assertEqual(s["n_episodes"], 3)
        self.assertEqual(s["n_pass"], 2)
        self.assertAlmostEqual(s["pct"], 200 / 3)
        self.assertEqual(s["levels"]["cause"]["n_pass"], 2)
        self.assertEqual(s["levels"]["held_state"]["n_applicable"], 3)
        self.assertEqual(s["levels"]["chunk_labels_1off"]["n_pass"], 3)
        self.assertEqual(s["n_semantic"], 2)
        self.assertAlmostEqual(s["by_failure_mode"]["drop_transport"]["pct"], 50.0)
        self.assertEqual(s["mean_calls"], 3)
        md = render_markdown({"methods": {"m": {"summary": s, "episodes": rows}}, "missing_references": [], "n_episodes": 3}, "dev", ["m"])
        self.assertIn("| m | 3 | 3 |", md)
        self.assertIn("| chunk_labels_1off |", md)
        self.assertIn("| semantic | overall |", md)
        self.assertIn("cause other vs ref grasp", md)
        self.assertIn("## Overall pass % by failure mode", md)

    def test_score_methods_reads_files_and_lists_missing(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            ref = make_reference()
            (td / "refs" / "ds").mkdir(parents=True)
            (td / "refs" / "ds" / "episode_000007.json").write_text(json.dumps(ref))
            (td / "refs" / "ds" / "episode_000008.json").write_text(json.dumps(make_reference(episode_index=8)))
            (td / "preds" / "m" / "ds").mkdir(parents=True)
            (td / "preds" / "m" / "ds" / "episode_000007.json").write_text(json.dumps(make_prediction()))
            out = score_methods(["m"], [("ds", 7), ("ds", 8), ("ds", 9)], ref_dir=td / "refs", pred_dir=td / "preds")
            self.assertEqual(out["missing_references"], [["ds", 9]])
            eps = out["methods"]["m"]["episodes"]
            self.assertEqual([e["pass"] for e in eps], [True, False])
            self.assertEqual(eps[1]["first_fail"], "missing")
            self.assertEqual(out["methods"]["m"]["summary"]["n_predicted"], 1)

    def test_load_episode_set(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "episodes_dev.json").write_text(json.dumps({"reference_version": "r1", "episodes": [{"dataset": "a", "episode_index": 1}]}))
            (td / "episodes.json").write_text(json.dumps({"reference_version": "r1", "episodes": [{"dataset": "a", "episode_index": 1}, {"dataset": "b", "episode_index": 2}]}))
            self.assertEqual(score.load_episode_set("dev", td), [("a", 1)])
            self.assertEqual(score.load_episode_set("heldout", td), [("a", 1), ("b", 2)])
            self.assertEqual(score.load_episode_set("all", td), [("a", 1), ("b", 2)])


class WholeP8MappingTests(unittest.TestCase):
    def record(self):
        return {
            "schema": "annot_v2", "dataset": "ds", "episode_index": 7, "n_chunks": 6, "source": "vlm",
            "identify": [{"chunk": 2, "held": "bowl_1", "gen": {"max_mem_gb": 17.0}}, {"chunk": 3, "held": "plate_1"},
                         {"chunk": 3, "held": "bowl_1"}, {"chunk": 4, "error": "no json"}],
            "gen": {"input_tokens": 6000, "max_mem_gb": 19.4},
            "refine": {"gen": {"max_mem_gb": 18.0}},
            "annotation": {
                "cause": "grasp",
                "landmarks": {"decisive_error": {"value": 4, "n_votes": 5, "spread": 1}, "failure_onset": {"value": None}},
                "chunk_label": ["progress", "uncertain", "progress", None, "failure_inducing", "aftermath"],
                "chunk_q": [1.0, 0.0, 0.8, 0.0, 0.6, 1.0],
            },
        }

    def test_mapping(self):
        p = record_to_prediction(self.record(), workdir="/w")
        self.assertEqual(p["chunk_labels"], ["progress", None, "progress", None, "failure_inducing", "aftermath"])
        self.assertEqual(p["chunk_q"], [1.0, 0.0, 0.8, 0.0, 0.6, 1.0])
        self.assertEqual(p["decisive_chunk"], 4)
        self.assertEqual(p["cause"], "grasp")
        self.assertEqual(p["held_object"], "bowl_1")
        self.assertEqual(p["held_obs"], [])
        self.assertEqual(p["events"], [])
        self.assertEqual(p["peak_mem_gb"], 19.4)
        self.assertEqual(p["raw_dir"], "/w")
        self.assertEqual(p["source"], "vlm")

    def test_mapping_without_annotation(self):
        rec = self.record()
        del rec["annotation"]
        rec["source"] = "vlm_failed"
        p = record_to_prediction(rec)
        self.assertEqual(p["chunk_labels"], [None] * 6)
        self.assertEqual(p["chunk_q"], [0.0] * 6)
        self.assertIsNone(p["decisive_chunk"])
        self.assertIsNone(p["cause"])
        self.assertEqual(p["held_object"], "bowl_1")
        p2 = record_to_prediction({"source": "vlm_failed"}, n_chunks=3)
        self.assertEqual(p2["chunk_labels"], [None, None, None])
        self.assertIsNone(p2["held_object"])
        self.assertIsNone(p2["peak_mem_gb"])

    def test_mapping_null_decisive_and_unknown_cause(self):
        rec = self.record()
        rec["annotation"]["landmarks"]["decisive_error"]["value"] = None
        rec["annotation"]["cause"] = "weird"
        p = record_to_prediction(rec)
        self.assertIsNone(p["decisive_chunk"])
        self.assertIsNone(p["cause"])

    def test_mapping_scores_against_reference(self):
        p = record_to_prediction(self.record())
        res = score_episode(make_reference(), p)
        self.assertEqual(res["levels"]["held_state"]["status"], "skip")
        self.assertEqual(res["levels"]["events"]["status"], "fail")  # no events emitted
        self.assertEqual(res["levels"]["held_object"]["status"], "pass")
        self.assertEqual(res["levels"]["chunk_labels"]["status"], "fail")  # chunks 1 and 3 abstained
        self.assertEqual(res["levels"]["chunk_labels_1off"]["status"], "fail")
        self.assertEqual(res["levels"]["chunk_labels_1off"]["n_wrong"], 2)
        self.assertEqual(res["levels"]["decisive"]["status"], "pass")
        self.assertEqual(res["levels"]["cause"]["status"], "pass")

    def test_build_args_matches_annotate_defaults(self):
        a = build_args(CONFIG)
        self.assertEqual((a.k, a.batch, a.tile_scale, a.temperature, a.max_new_tokens, a.max_tiles), (5, 3, 1.5, 0.7, 1200, 40))
        self.assertTrue(a.refine and a.include_clean)
        self.assertFalse(a.no_identify or a.dry_run or a.save_render)
        self.assertEqual(a.model, "Qwen/Qwen3-VL-8B-Instruct")
        b = build_args({**CONFIG, "model": "x"})
        self.assertEqual(b.model, "x")


class RegistryTests(unittest.TestCase):
    def test_registry_names(self):
        self.assertEqual(set(REGISTRY), {"whole_p8", "event_first_v1", "event_first_batched", "event_first_v2", "telem_v3", "telem_v3c", "telem_v4", "telem_v4nv", "telem_v4s", "fused_v4",
                                         "oracle_rules", "oracle_whole", "oracle_chunk", "oracle_moment"})
        mod = load_method("whole_p8")
        self.assertTrue(callable(mod.run))
        self.assertIsInstance(mod.CONFIG, dict)

    def test_unknown_and_missing(self):
        with self.assertRaises(KeyError):
            load_method("nope")
        import methods as m
        m.REGISTRY["_ghost"] = "methods._ghost_module"
        try:
            with self.assertRaises(ImportError) as cm:
                load_method("_ghost")
            self.assertIn("_ghost_module", str(cm.exception))
        finally:
            del m.REGISTRY["_ghost"]


class HarnessTests(unittest.TestCase):
    def test_call_counter_and_null_prediction(self):
        import run_method

        class FakeBackend:
            def __init__(self):
                self.last = {}

            def generate(self, system, content, k=5, **kw):
                return ["x"] * k

            def generate_many(self, system, contents, **kw):
                return ["y"] * len(contents)

        b = FakeBackend()
        c = run_method.CallCounter(b)
        b.generate("s", [], k=3)
        b.generate("s", [], k=2, temperature=0.0)
        b.generate_many("s", [1, 2, 3, 4])
        self.assertEqual((c.calls, c.prompts), (3, 9))
        c.reset()
        self.assertEqual((c.calls, c.prompts), (0, 0))
        p = run_method.null_prediction(4)
        self.assertEqual(p["chunk_labels"], [None] * 4)
        out = run_method.finalize({"chunk_labels": [None], "error": "E"}, "m", {"a": 1}, "ds", 3, 2.34, c, Path("/w"))
        self.assertEqual((out["method"], out["dataset"], out["episode_index"], out["wall_s"], out["n_model_calls"]), ("m", "ds", 3, 2.3, 0))
        self.assertEqual(out["raw_dir"], "/w")
        for k in run_method.PRED_FIELDS:
            self.assertIn(k, out)

    def test_parse_episode_args(self):
        import run_method
        self.assertEqual(run_method.parse_episode_args(["full_shift8__t0:12", "a:b:3"]), [("full_shift8__t0", 12), ("a:b", 3)])

    def test_gpu_guard_excludes_self(self):
        import run_method
        if not Path("/proc").exists():
            self.skipTest("no /proc")
        # this test process's own command line may contain 'test_bench.py' only; the pattern must not match ourselves
        self.assertNotIn(os.getpid(), run_method.other_gpu_processes("test_bench.py"))


if __name__ == "__main__":
    unittest.main()
