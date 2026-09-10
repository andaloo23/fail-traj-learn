"""CPU unit tests for oracle_labels.py on a stub reference: q mapping, per-frame expansion, event_type_in_chunk, episode row.

Run: run_tests.sh (unittest discover under scripts/annotate/bench)
"""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oracle_labels as ol  # noqa: E402
from oracle_labels import episode_row, event_type_by_chunk, failure_onset_chunk, frame_table, held_by_frame, q_of  # noqa: E402


def stub_reference(**over):
    """drop_transport episode, 6 chunks of 10 frames (last one 8 frames): held 20..39, drop in chunk 4, regrasp in chunk 5."""
    ref = {
        "reference_version": "r2", "dataset": "ds__t0", "episode_index": 7, "success": False,
        "n_frames": 58, "n_chunks": 6, "chunks": [[0, 10], [10, 20], [20, 30], [30, 40], [40, 50], [50, 58]],
        "held_runs": [
            {"start": 0, "end": 17, "state": "empty", "object": None},
            {"start": 18, "end": 21, "state": "ambiguous", "object": "bowl_1"},
            {"start": 22, "end": 37, "state": "held", "object": "bowl_1"},
            {"start": 38, "end": 41, "state": "ambiguous", "object": "bowl_1"},
            {"start": 42, "end": 57, "state": "empty", "object": None},
        ],
        "events": [
            {"index": 20, "type": "grasp", "object": "bowl_1", "last_before": 19, "first_after": 20, "chunk": 1},
            {"index": 40, "type": "drop", "object": "bowl_1", "last_before": 39, "first_after": 40, "chunk": 3},
            {"index": 52, "type": "grasp", "object": "bowl_1", "last_before": 51, "first_after": 52, "chunk": 5},
            {"index": 56, "type": "release", "object": "bowl_1", "last_before": 55, "first_after": 56, "chunk": 5},
        ],
        "failure_mode": "drop_transport", "cause": "grasp", "decisive_chunk": 3,
        "chunk_labels": [
            {"chunk": 0, "allowed": ["progress"], "primary": "progress", "rule": "advance_approach"},
            {"chunk": 1, "allowed": ["progress", "neutral"], "primary": "progress", "rule": "pre_other"},
            {"chunk": 2, "allowed": ["neutral"], "primary": "neutral", "rule": "idle"},
            {"chunk": 3, "allowed": ["failure_inducing"], "primary": "failure_inducing", "rule": "decisive"},
            {"chunk": 4, "allowed": ["neutral", "aftermath", "recovery"], "primary": "aftermath", "rule": "post_recoverable"},
            {"chunk": 5, "allowed": ["recovery"], "primary": "recovery", "rule": "regrasp"},
        ],
    }
    ref.update(over)
    return ref


class QMappingTests(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual(q_of(["progress"], "advance_approach"), 1.0)
        self.assertEqual(q_of(["progress", "neutral"], "pre_other"), 0.5)
        self.assertEqual(q_of(["neutral", "aftermath", "recovery"], "post_recoverable"), 0.25)
        self.assertEqual(q_of(["progress", "recovery", "neutral", "aftermath"], "post_held_unscorable"), 0.25)
        self.assertEqual(q_of(["failure_inducing", "neutral"], "decisive+decisive_boundary"), 0.5)

    def test_unlocalised_is_zero_whatever_the_set(self):
        self.assertEqual(q_of(["failure_inducing", "neutral", "progress"], "unlocalised"), 0.0)
        self.assertEqual(q_of(["progress"], "unlocalised_other"), 0.0)
        self.assertEqual(q_of(list("abcde"), "unlocalised_hold_no_release"), 0.0)
        self.assertEqual(q_of(["progress"], "advance_approach+unlocalised"), 1.0)  # only the base rule counts


class FrameExpansionTests(unittest.TestCase):
    def test_rows_and_columns(self):
        ref = stub_reference()
        df = frame_table(ref, g0=1000)
        self.assertEqual(len(df), 58)
        self.assertEqual(df["frame_index"].tolist(), list(range(58)))
        self.assertEqual(df["global_index"].tolist(), list(range(1000, 1058)))
        self.assertEqual(df["chunk"].tolist(), [0] * 10 + [1] * 10 + [2] * 10 + [3] * 10 + [4] * 10 + [5] * 8)
        self.assertEqual(df["label"].iloc[0], "progress"); self.assertEqual(df["label"].iloc[35], "failure_inducing")
        self.assertEqual(df["label"].iloc[57], "recovery")
        self.assertEqual(df["allowed"].iloc[45], "neutral|aftermath|recovery")
        self.assertEqual(df["q"].tolist()[::10], [1.0, 0.5, 1.0, 1.0, 0.25, 1.0])
        self.assertTrue((df["dataset"] == "ds__t0").all()); self.assertTrue((df["episode_index"] == 7).all())
        self.assertTrue((df["source"] == ol.SOURCE).all()); self.assertEqual(ol.SOURCE, "oracle_r6"); self.assertFalse(df["success"].any())
        self.assertTrue((df["cause"] == "grasp").all()); self.assertTrue((df["failure_mode"] == "drop_transport").all())
        for k in ("dataset", "episode_index", "frame_index", "global_index", "chunk", "label", "allowed", "q", "cause", "failure_mode",
                  "decisive_error_chunk", "failure_onset_chunk", "visible_failure_chunk", "recoverable_until_chunk",
                  "event_type_in_chunk", "event_at_frame", "event_target", "event_hold_frames",
                  "event_missed_release", "held", "success", "source"):
            self.assertIn(k, df.columns)

    def test_events_land_on_their_own_frame(self):
        """The RL `events` reward reads these columns; `event_type_in_chunk` spans a whole chunk and
        cannot say when inside it the grasp happened (docs/rl_verification.md finding 1)."""
        ref = stub_reference(target_slot="bowl_1")
        for ev, hold in zip(ref["events"], (18, 18, 4, 4)):
            ev["hold_frames"] = hold
        df = frame_table(ref, 0)
        at = df["event_at_frame"].tolist()
        self.assertEqual({i: at[i] for i in (20, 40, 52, 56)},
                         {20: "grasp", 40: "drop", 52: "grasp", 56: "release"})
        self.assertEqual([i for i, k in enumerate(at) if k != "none"], [20, 40, 52, 56])
        self.assertEqual(df["event_hold_frames"].tolist()[20], 18)
        self.assertTrue(df["event_target"].iloc[[20, 40, 52, 56]].all())
        # the episode failed, so its one release did not put the bowl where the task wanted it
        self.assertEqual(df.index[df["event_missed_release"]].tolist(), [56])

    def test_the_release_that_completes_a_successful_episode_is_not_missed(self):
        ref = stub_reference(target_slot="bowl_1", success=True)
        df = frame_table(ref, 0)
        self.assertFalse(df["event_missed_release"].any())

    def test_events_on_other_objects_are_not_on_the_target(self):
        ref = stub_reference(target_slot="plate_1")
        df = frame_table(ref, 0)
        self.assertFalse(df["event_target"].any())
        self.assertFalse(df["event_missed_release"].any())

    def test_landmarks(self):
        ref = stub_reference()
        df = frame_table(ref, 0)
        self.assertTrue((df["decisive_error_chunk"] == 3).all())
        self.assertTrue((df["visible_failure_chunk"] == 3).all())
        self.assertTrue(df["recoverable_until_chunk"].isna().all())
        self.assertTrue((df["failure_onset_chunk"] == 3).all())
        # an earlier {failure_inducing} chunk is the onset; decisive stays t*
        ref2 = stub_reference()
        ref2["chunk_labels"][1] = {"chunk": 1, "allowed": ["failure_inducing"], "primary": "failure_inducing", "rule": "other_event"}
        self.assertEqual(failure_onset_chunk(ref2), 1)
        df2 = frame_table(ref2, 0)
        self.assertTrue((df2["failure_onset_chunk"] == 1).all()); self.assertTrue((df2["decisive_error_chunk"] == 3).all())
        # null decisive and no error chunk -> onset null, Int64 dtype keeps the column nullable
        ref3 = stub_reference(decisive_chunk=None, failure_mode="never_reached", cause="reaching",
                              chunk_labels=[{"chunk": c, "allowed": ["failure_inducing", "neutral", "progress"], "primary": "neutral", "rule": "unlocalised"} for c in range(6)])
        df3 = frame_table(ref3, 0)
        self.assertTrue(df3["decisive_error_chunk"].isna().all()); self.assertTrue(df3["failure_onset_chunk"].isna().all())
        self.assertTrue((df3["q"] == 0.0).all())
        self.assertEqual(str(df3["decisive_error_chunk"].dtype), "Int64")

    def test_event_type_in_chunk_and_held(self):
        ref = stub_reference()
        self.assertEqual(event_type_by_chunk(ref), {1: "grasp", 3: "drop", 5: "grasp"})  # first event of chunk 5 is the grasp
        df = frame_table(ref, 0)
        by_chunk = df.drop_duplicates("chunk").set_index("chunk")["event_type_in_chunk"].to_dict()
        self.assertEqual(by_chunk, {0: "none", 1: "grasp", 2: "none", 3: "drop", 4: "none", 5: "grasp"})
        held = held_by_frame(ref)
        self.assertEqual(held.sum(), 16)
        self.assertTrue(held[22:38].all()); self.assertFalse(held[:22].any()); self.assertFalse(held[38:].any())  # ambiguous is not held
        np.testing.assert_array_equal(df["held"].to_numpy(), held)

    def test_success_reference(self):
        ref = stub_reference(success=True, failure_mode="success", cause="unclear", decisive_chunk=None,
                             chunk_labels=[{"chunk": 0, "allowed": ["progress"], "primary": "progress", "rule": "advance_approach"},
                                           {"chunk": 1, "allowed": ["progress"], "primary": "progress", "rule": "advance_hold"},
                                           {"chunk": 2, "allowed": ["progress"], "primary": "progress", "rule": "advance_transporting"},
                                           {"chunk": 3, "allowed": ["progress"], "primary": "progress", "rule": "place_release"},
                                           {"chunk": 4, "allowed": ["progress"], "primary": "progress", "rule": "advance_placed"},
                                           {"chunk": 5, "allowed": ["neutral", "aftermath"], "primary": "neutral", "rule": "post_success"}])
        df = frame_table(ref, 5)
        self.assertTrue(df["success"].all()); self.assertTrue((df["failure_mode"] == "success").all())
        self.assertEqual(df["label"].iloc[-1], "neutral"); self.assertEqual(df["q"].iloc[-1], 0.5)
        self.assertTrue(df["decisive_error_chunk"].isna().all()); self.assertTrue(df["failure_onset_chunk"].isna().all())
        row = episode_row(ref)
        self.assertEqual((row["n_chunks"], row["n_events"], row["n_failure_inducing"]), (6, 4, 0))
        self.assertAlmostEqual(row["frac_q1"], 5 / 6)

    def test_inconsistent_reference_is_rejected(self):
        ref = stub_reference()
        ref["chunk_labels"] = ref["chunk_labels"][:-1]
        with self.assertRaises(ValueError):
            frame_table(ref, 0)
        ref2 = stub_reference(n_frames=60)
        with self.assertRaises(ValueError):
            frame_table(ref2, 0)


class EpisodeRowTests(unittest.TestCase):
    def test_fields(self):
        row = episode_row(stub_reference())
        self.assertEqual(row["dataset"], "ds__t0"); self.assertEqual(row["episode_index"], 7)
        self.assertEqual((row["success"], row["failure_mode"], row["cause"], row["decisive_chunk"]), (False, "drop_transport", "grasp", 3))
        self.assertEqual((row["n_chunks"], row["n_events"], row["n_failure_inducing"]), (6, 4, 1))
        self.assertAlmostEqual(row["frac_q1"], 4 / 6)


class DatasetIndexTests(unittest.TestCase):
    def test_dataset_from_index_reads_meta_parquet(self):
        with tempfile.TemporaryDirectory() as td:
            old = ol.DATA
            try:
                ol.DATA = Path(td)
                d = Path(td) / "ds__t0" / "meta" / "episodes" / "chunk-000"
                d.mkdir(parents=True)
                pd.DataFrame({"episode_index": [0, 1, 2], "dataset_from_index": [0, 120, 250], "dataset_to_index": [120, 250, 400]}).to_parquet(d / "file-000.parquet")
                self.assertEqual(ol.dataset_from_index("ds__t0"), {0: 0, 1: 120, 2: 250})
                with self.assertRaises(FileNotFoundError):
                    ol.dataset_from_index("nope")
            finally:
                ol.DATA = old


if __name__ == "__main__":
    unittest.main()
