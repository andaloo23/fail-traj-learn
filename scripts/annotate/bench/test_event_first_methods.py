"""CPU checks for the event-first benchmark adapters (fake backend, stub episode, no model).

Run (WSL): python -m unittest discover -s scripts/annotate/bench -p test_event_first_methods.py
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
for _p in (_HERE / "methods", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _event_first_lib as lib  # noqa: E402
import event_first_batched  # noqa: E402
import event_first_v1  # noqa: E402
from local_segmenter import SYSTEM as CHUNK_SYSTEM  # noqa: E402
from prompt import IDENTIFY_SYSTEM  # noqa: E402
from segmentation_lab import STATE_SYSTEM  # noqa: E402

CONTRACT_KEYS = {"held_obs", "events", "held_object", "chunk_labels", "chunk_q", "decisive_chunk", "cause", "n_model_calls", "peak_mem_gb", "raw_dir"}


class StubEpisode:
    """Only the non-privileged surface of common.Episode. col() refuses any priv.* key."""

    def __init__(self, n_chunks, held=(60, 124), release_at=None, chunk_len=10):
        self.n = n_chunks * chunk_len
        self.fps = 20
        self.chunks = [(c * chunk_len, (c + 1) * chunk_len) for c in range(n_chunks)]
        self.name, self.ep = "stub", 0
        self.meta = {"object_slots": ["alphabet_soup_1", "cream_cheese_1", "basket_1"], "fixtures": ["flat_stove"],
                     "target_objects": ["alphabet_soup_1"], "task_language": "put the alphabet soup in the basket"}
        self.task = self.meta["task_language"]
        self.held = held
        self.gripper_cmd = np.full(self.n, -1.0)
        if held is not None:
            self.gripper_cmd[held[0] - 3:] = 1.0
        if release_at is not None:
            self.gripper_cmd[release_at:] = -1.0
        self.eef_xyz = np.zeros((self.n, 3))
        self.accessed = []
        self.frames_seen = []

    @property
    def n_chunks(self):
        return len(self.chunks)

    def chunk_of_frame(self, i):
        for c, (a, b) in enumerate(self.chunks):
            if a <= i < b:
                return c
        return self.n_chunks - 1

    def frame(self, i):
        assert 0 <= i < self.n, f"frame {i} out of range"
        self.frames_seen.append(int(i))
        im = np.zeros((32, 32, 3), dtype=np.uint8)
        im[:, :, 0] = int(i) % 251  # frame-specific bytes so the input hash distinguishes frames
        return im, im.copy()

    def col(self, key):
        self.accessed.append(key)
        if key.startswith("priv."):
            raise AssertionError(f"privileged column accessed: {key}")
        return np.zeros((self.n, 1))

    def is_held(self, i):
        return self.held is not None and self.held[0] <= i <= self.held[1]


class FakeBackend:
    """Canned JSON per prompt family; records how it was called."""

    def __init__(self, ep, chunk_label="progress", identify="alphabet soup"):
        self.ep = ep
        self.chunk_label = chunk_label
        self.identify = identify
        self.generate_calls = 0
        self.generate_many_calls = 0
        self.generate_many_prompts = 0
        self.systems = []
        self.chunk_texts = []
        self.last = {"gen_s": 0.1, "max_mem_gb": 1.5}

    def manual_seed(self, value):
        self.seed = value

    def _answer(self, system, content):
        text = "\n".join(b["text"] for b in content if b["type"] == "text")
        if system == STATE_SYSTEM:
            frame = int(text.split("Frame ")[1].split(",")[0])
            state = "held" if self.ep.is_held(frame) else "empty"
            return json.dumps({"states": [{"frame": frame, "state": state, "object": "blue can" if state == "held" else None}]})
        if system == CHUNK_SYSTEM:
            self.chunk_texts.append(text)
            return json.dumps({"label": self.chunk_label, "object": "alphabet soup", "observation": "gripper moves toward the can", "event": "approach"})
        if system == IDENTIFY_SYSTEM:
            return json.dumps({"held_object": self.identify, "appearance": "dark blue can", "confidence": 0.9})
        raise AssertionError("unexpected system prompt")

    def generate(self, system, content, k=1, temperature=0.0, max_new_tokens=100, batch=1, **kw):
        self.generate_calls += 1
        self.systems.append(system)
        return [self._answer(system, content) for _ in range(k)]

    def generate_many(self, system, contents, temperature=0.0, max_new_tokens=100, batch=8, **kw):
        self.generate_many_calls += 1
        self.generate_many_prompts += len(contents)
        self.systems.append(system)
        self.last = {"n_prompts": len(contents), "batches": -(-len(contents) // batch), "gen_s": 0.5, "max_mem_gb": 3.0}
        return [self._answer(system, c) for c in contents]


def run_method(method, ep, backend, workdir):
    return method.run(ep, backend, Path(workdir) / method.__name__)


class EventFirstMethodTests(unittest.TestCase):
    def test_drop_when_command_stays_closed(self):
        ep = StubEpisode(28)
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_method(event_first_v1, ep, FakeBackend(ep), tmp)
        types = [(e["type"], e["last_before"], e["first_after"]) for e in pred["events"]]
        self.assertEqual(types, [("grasp", 59, 60), ("drop", 124, 125)])
        self.assertEqual(pred["decisive_chunk"], 12)
        self.assertEqual(pred["cause"], "grasp")
        self.assertEqual(pred["chunk_labels"][12], "failure_inducing")
        self.assertEqual(pred["held_object"], "alphabet_soup_1")
        self.assertEqual(pred["events"][1]["object"], "alphabet_soup_1")

    def test_release_when_command_opens(self):
        ep = StubEpisode(28, release_at=123)
        with tempfile.TemporaryDirectory() as tmp:
            pred = run_method(event_first_v1, ep, FakeBackend(ep), tmp)
        self.assertEqual([e["type"] for e in pred["events"]], ["grasp", "release"])
        self.assertIsNone(pred["decisive_chunk"])
        self.assertEqual(pred["cause"], "manipulation")
        self.assertNotEqual(pred["chunk_labels"][12], "failure_inducing")

    def test_no_events_gives_null_decisive_and_cause(self):
        ep = StubEpisode(13, held=None)
        with tempfile.TemporaryDirectory() as tmp:
            backend = FakeBackend(ep)
            pred = run_method(event_first_v1, ep, backend, tmp)
        self.assertEqual(pred["events"], [])
        self.assertIsNone(pred["held_object"])
        self.assertIsNone(pred["decisive_chunk"])
        self.assertIsNone(pred["cause"])
        self.assertNotIn(IDENTIFY_SYSTEM, backend.systems)

    def test_chunk_count_independence_and_contract_shape(self):
        for n_chunks in (13, 52):
            for method in (event_first_v1, event_first_batched):
                with self.subTest(n_chunks=n_chunks, method=method.__name__):
                    ep = StubEpisode(n_chunks)
                    with tempfile.TemporaryDirectory() as tmp:
                        pred = run_method(method, ep, FakeBackend(ep), tmp)
                    self.assertTrue(CONTRACT_KEYS.issubset(pred))
                    self.assertEqual(len(pred["chunk_labels"]), n_chunks)
                    self.assertEqual(len(pred["chunk_q"]), n_chunks)
                    self.assertTrue(all(0 <= o["frame"] < ep.n for o in pred["held_obs"]))
                    self.assertEqual(max(o["frame"] for o in pred["held_obs"]), ep.n - 1)
                    self.assertTrue(all(o["state"] in ("held", "empty", "uncertain") and o["object"] is None for o in pred["held_obs"]))
                    self.assertTrue(all(0 <= f < ep.n for f in ep.frames_seen))
                    self.assertTrue(all(lab in ("progress", "failure_inducing", "recovery", "neutral", "aftermath", None) for lab in pred["chunk_labels"]))
                    self.assertTrue(all(q == 0.0 for q, lab in zip(pred["chunk_q"], pred["chunk_labels"]) if lab is None))
                    self.assertTrue(all(q > 0.0 for q, lab in zip(pred["chunk_q"], pred["chunk_labels"]) if lab is not None))
                    self.assertEqual(pred["decisive_chunk"], 12)
                    self.assertEqual(pred["chunk_labels"][12], "failure_inducing")

    def test_v1_call_budget_and_batched_uses_generate_many(self):
        ep = StubEpisode(28)
        with tempfile.TemporaryDirectory() as tmp:
            b1 = FakeBackend(ep)
            run_method(event_first_v1, ep, b1, tmp)
            self.assertEqual(b1.generate_many_calls, 0)
            # 57 + 57 scan frames, 2 transitions x 10 frames x 3 repeats, 28 x 2 chunk passes, 4 identify
            self.assertEqual(b1.generate_calls, 57 + 57 + 60 + 56 + 4)
            b2 = FakeBackend(ep)
            pred = run_method(event_first_batched, ep, b2, tmp)
            self.assertEqual(b2.generate_many_calls, 2 + 3)
            self.assertEqual(b2.generate_many_prompts, 57 + 57 + 60)
            self.assertEqual(b2.generate_calls, 56 + 4)
            self.assertEqual(pred["n_model_calls"], 5 + 56 + 4)
            self.assertEqual(pred["peak_mem_gb"], 3.0)

    def test_batched_adds_held_object_fact_and_v1_does_not(self):
        ep = StubEpisode(28)
        with tempfile.TemporaryDirectory() as tmp:
            b1, b2 = FakeBackend(ep), FakeBackend(ep)
            run_method(event_first_v1, ep, b1, tmp)
            run_method(event_first_batched, ep, b2, tmp)
        self.assertTrue(all("wrist close-up identification" not in t for t in b1.chunk_texts))
        self.assertTrue(all("alphabet soup" in t and "wrist close-up identification" in t for t in b2.chunk_texts))
        self.assertTrue(all("Object appearances:" in t and "stove" in t for t in b2.chunk_texts))  # fixtures reach the glossary

    def test_cache_hit_skips_backend(self):
        ep = StubEpisode(28)
        with tempfile.TemporaryDirectory() as tmp:
            first = run_method(event_first_v1, ep, FakeBackend(ep), tmp)
            again = FakeBackend(ep)
            second = run_method(event_first_v1, ep, again, tmp)
            self.assertEqual(again.generate_calls, 0)
            self.assertEqual(again.generate_many_calls, 0)
            self.assertEqual(second["n_model_calls"], 0)
            for key in ("held_obs", "events", "held_object", "chunk_labels", "chunk_q", "decisive_chunk", "cause"):
                self.assertEqual(first[key], second[key])
            cached = list(Path(tmp).rglob("*.json"))
            self.assertGreaterEqual(len(cached), 57 + 57 + 60 + 56 + 4)

    def test_privileged_columns_are_never_read(self):
        ep = StubEpisode(13)
        with self.assertRaises(AssertionError):
            ep.col("priv.obj_grasped")  # the guard is live
        ep.accessed = []
        with tempfile.TemporaryDirectory() as tmp:
            run_method(event_first_v1, ep, FakeBackend(ep), tmp)
            run_method(event_first_batched, ep, FakeBackend(ep), tmp)
        self.assertEqual(ep.accessed, [])

    def test_scan_frames_and_refine_window(self):
        self.assertEqual(lib.scan_frame_set(130, 5, 2)[:3], [2, 7, 12])
        self.assertEqual(lib.scan_frame_set(130, 5, 2)[-2:], [127, 129])
        self.assertEqual(lib.scan_frame_set(280, 5, 0)[-1], 279)
        ep = StubEpisode(13)
        frames = lib.refine_frames(ep, [{"last_before_frame": 120, "first_after_frame": 125}])
        self.assertEqual(frames, list(range(118, 128)))
        self.assertEqual(lib.refine_frames(ep, [{"last_before_frame": 127, "first_after_frame": 129}])[-1], 129)

    def test_slot_matching_and_tie(self):
        slots = ["alphabet_soup_1", "cream_cheese_1"]
        self.assertEqual(lib.match_slot("alphabet soup", slots), "alphabet_soup_1")
        self.assertEqual(lib.match_slot("cream_cheese_1", slots), "cream_cheese_1")
        self.assertIsNone(lib.match_slot("basket", slots))
        self.assertIsNone(lib.match_slot(None, slots))
        self.assertEqual(lib.decisive_and_cause([{"type": "grasp", "chunk": 5}, {"type": "drop", "chunk": 9}, {"type": "grasp", "chunk": 11}]), (9, "grasp"))
        self.assertEqual(lib.decisive_and_cause([{"type": "grasp", "chunk": 5}, {"type": "release", "chunk": 20}]), (None, "manipulation"))
        self.assertEqual(lib.decisive_and_cause([{"type": "grasp", "chunk": 5}]), (None, None))

    def test_configs(self):
        self.assertEqual(event_first_v1.CONFIG["backend"], "generate")
        self.assertEqual(event_first_batched.CONFIG["backend"], "generate_many")
        self.assertFalse(event_first_v1.CONFIG["chunk"]["held_object_fact"])
        self.assertTrue(event_first_batched.CONFIG["chunk"]["held_object_fact"])
        self.assertEqual(event_first_v1.CONFIG["scan"]["offsets"], [0, 2])
        self.assertEqual([p["seed"] for p in event_first_batched.CONFIG["chunk_passes"]], [7100, 9100])
        json.dumps(event_first_batched.CONFIG)


if __name__ == "__main__":
    unittest.main()
