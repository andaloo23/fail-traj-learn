"""CPU checks for the fused_v4 adapter (fake backend with canned per-frame states, stub episode with an explicit
command / aperture schedule, no model).

Run (WSL): python -m unittest discover -s scripts/annotate/bench -p test_fused_v4.py
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

import event_first_v2 as v2  # noqa: E402
import fused_v4 as m  # noqa: E402
from segmentation_lab import STATE_SYSTEM  # noqa: E402
from test_event_first_methods import CONTRACT_KEYS, FakeBackend, StubEpisode  # noqa: E402

OPEN, HELD, CLOSED = 0.04, 0.02, 0.001
TRAVEL = [0.03, 0.02, 0.012, 0.011]  # aperture on the first 4 frames of every CLOSE run (fingers travelling)
CC = m.CONFIG["candidates"]
VC = m.CONFIG["verify"]


class Ep(StubEpisode):
    """StubEpisode with an explicit command schedule and aperture.

    close: [(first, last)] frames with command CLOSE; the aperture is OPEN elsewhere, TRAVEL on the first 4 frames of
    a run and HELD afterwards, then overridden by aperture=[(first, last, value)]. held: [(first, last)] frames on
    which the fake VLM answers held. moving: [(start, end)] ranges with 3 mm/frame eef motion.
    """

    def __init__(self, n_chunks, close=(), aperture=(), held=(), moving=(), chunk_len=10):
        super().__init__(n_chunks, held=None, chunk_len=chunk_len)
        n = self.n
        cmd = np.full(n, -1.0)
        ap = np.full(n, OPEN)
        for a, b in close:
            cmd[a:b + 1] = 1.0
            for k, v in enumerate(TRAVEL):
                if a + k <= b:
                    ap[a + k] = v
            ap[a + len(TRAVEL):b + 1] = HELD
        for a, b, v in aperture:
            ap[a:b + 1] = v
        self.gripper_cmd, self.gripper_aperture = cmd, ap
        self.held_frames = set()
        for a, b in held:
            self.held_frames.update(range(a, b + 1))
        eef = np.zeros((n, 3))
        for f in range(1, n):
            eef[f] = eef[f - 1]
            if any(s <= f - 1 < e for s, e in moving):
                eef[f, 0] += 0.003
        self.eef_xyz = eef

    def is_held(self, i):
        return int(i) in self.held_frames


class Backend(FakeBackend):
    """FakeBackend whose held/empty answer can be overridden per frame ("garbage" = malformed JSON)."""

    def __init__(self, ep, states=None, **kw):
        super().__init__(ep, **kw)
        self.states = dict(states or {})
        self.state_frames = []

    def _answer(self, system, content):
        if system == STATE_SYSTEM:
            text = "\n".join(b["text"] for b in content if b["type"] == "text")
            frame = int(text.split("Frame ")[1].split(",")[0])
            self.state_frames.append(frame)
            if frame in self.states:
                st = self.states[frame]
                if st == "garbage":
                    return "I cannot tell."
                return json.dumps({"states": [{"frame": frame, "state": st, "object": None}]})
        return super()._answer(system, content)


def run(ep, backend, tmp, cfg=m.CONFIG):
    return m.run(ep, backend, Path(tmp) / "fused_v4", cfg)


def result_of(tmp):
    return json.loads((Path(tmp) / "fused_v4" / "result.json").read_text())


def drop_ep(n_chunks=28, **kw):
    """Close from 57 to the end, object held 61..124 (aperture 2 cm), lost at 125 while still squeezing (0.1 cm)."""
    n = n_chunks * 10
    kw.setdefault("held", [(61, 124)])
    kw.setdefault("moving", [(0, 125)])
    return Ep(n_chunks, close=[(57, n - 1)], aperture=[(125, n - 1, CLOSED)], **kw)


def spans(segments):
    return [(s["start"], s["end"], s["end_reason"]) for s in segments]


def event_tuples(pred):
    return [(e["type"], e["last_before"], e["first_after"]) for e in pred["events"]]


# ------------------------------------------------------------------ 1. candidates
class CandidateTests(unittest.TestCase):
    def test_close_runs_min_length_and_trim(self):
        ep = Ep(13, close=[(10, 17), (30, 36), (50, 99)])  # 8, 7 and 50 frames
        self.assertEqual(m.close_runs(ep.gripper_cmd, CC["close_min_run"]), [(10, 17), (50, 99)])
        segs = m.candidate_segments(ep.gripper_aperture, ep.gripper_cmd, CC)
        self.assertEqual(spans(segs), [(14, 17, "open"), (54, 99, "open")])
        self.assertEqual([s["n_frames"] for s in segs], [4, 46])
        self.assertEqual([s["index"] for s in segs], [0, 1])
        self.assertEqual(segs[1]["run"], [50, 99])
        self.assertAlmostEqual(segs[1]["median_aperture_m"], HELD)

    def test_split_point_when_object_is_lost_while_squeezing(self):
        ep = drop_ep(28)
        segs = m.candidate_segments(ep.gripper_aperture, ep.gripper_cmd, CC)
        self.assertEqual(spans(segs), [(61, 124, "split"), (125, 279, "episode_end")])
        self.assertEqual([s["part"] for s in segs], [0, 1])
        self.assertAlmostEqual(segs[1]["median_aperture_m"], CLOSED)

    def test_early_collapse_is_a_close_on_nothing_not_a_split(self):
        # fingers reach 0.1 cm two frames after the trimmed start: the whole run is one closed-empty candidate
        ep = Ep(13, close=[(70, 129)], aperture=[(76, 129, CLOSED)])
        segs = m.candidate_segments(ep.gripper_aperture, ep.gripper_cmd, CC)
        self.assertEqual(spans(segs), [(74, 129, "episode_end")])
        self.assertAlmostEqual(segs[0]["median_aperture_m"], CLOSED)
        # exactly at the minimum pre length the split is taken
        ep2 = Ep(13, close=[(70, 129)], aperture=[(80, 129, CLOSED)])
        self.assertEqual(spans(m.candidate_segments(ep2.gripper_aperture, ep2.gripper_cmd, CC)), [(74, 79, "split"), (80, 129, "episode_end")])

    def test_split_needs_a_prior_wide_aperture_and_a_lasting_collapse(self):
        # closed on nothing from the start with a wobble to 0.35 cm: no segment ever reached 0.6 cm -> no split
        ep = Ep(28, close=[(57, 279)], aperture=[(61, 279, CLOSED), (150, 151, 0.0035)])
        self.assertEqual(spans(m.candidate_segments(ep.gripper_aperture, ep.gripper_cmd, CC)), [(61, 279, "episode_end")])
        # a collapse of 5 frames followed by the command opening is not a split (the segment ends by opening)
        ep2 = Ep(28, close=[(57, 129)], aperture=[(125, 129, CLOSED)])
        self.assertEqual(spans(m.candidate_segments(ep2.gripper_aperture, ep2.gripper_cmd, CC)), [(61, 129, "open")])
        # 6 collapsed frames before the opening are a split
        ep3 = Ep(28, close=[(57, 130)], aperture=[(125, 130, CLOSED)])
        self.assertEqual(spans(m.candidate_segments(ep3.gripper_aperture, ep3.gripper_cmd, CC)), [(61, 124, "split"), (125, 130, "open")])

    def test_judge_frames_dedupe_and_clamp(self):
        self.assertEqual(m.judge_frames({"start": 61, "end": 124}), [65, 92, 122])
        self.assertEqual(m.judge_frames({"start": 14, "end": 17}), [15, 17])     # 4-frame candidate: start+4 clamps to end
        self.assertEqual(m.judge_frames({"start": 10, "end": 15}), [12, 13, 14])  # 6-frame post-split segment
        self.assertEqual(m.judge_frames({"start": 5, "end": 5}), [5])

    def test_budget_keeps_the_longest_six(self):
        closes = [(10 + 20 * i, 10 + 20 * i + 7 + i) for i in range(8)]  # run lengths 8..15, all judged held by the VLM
        ep = Ep(28, close=closes, held=[(0, 279)])
        segs = m.candidate_segments(ep.gripper_aperture, ep.gripper_cmd, CC)
        self.assertEqual(len(segs), 8)
        judged = m.select_judged(segs, CC["max_judged"])
        self.assertEqual([s["index"] for s in judged], [2, 3, 4, 5, 6, 7])
        self.assertEqual(segs[0]["judge_frames"], [])
        with tempfile.TemporaryDirectory() as tmp:
            backend = Backend(ep)
            pred = run(ep, backend, tmp)
            res = result_of(tmp)
        self.assertEqual(backend.generate_many_calls, 1)
        self.assertEqual(backend.generate_many_prompts, sum(len(m.judge_frames(s)) for s in segs[2:]))
        self.assertEqual([c["decided_by"] for c in res["evidence"]["candidates"]], ["over_budget"] * 2 + ["vote"] * 6)
        self.assertEqual([c["state"] for c in res["evidence"]["candidates"]], ["uncertain"] * 2 + ["held"] * 6)
        states = [o["state"] for o in pred["held_obs"]]
        self.assertEqual(states[14:18], ["uncertain"] * 4)  # run 0 trimmed frames
        self.assertEqual(states[10:14], ["empty"] * 4)      # fingers travelling
        self.assertEqual(len([e for e in pred["events"] if e["type"] == "grasp"]), 6)


# ------------------------------------------------------------------ 2. fusion
class FusionTests(unittest.TestCase):
    def seg(self, start=61, end=124, judged=True):
        s = {"index": 0, "start": start, "end": end, "n_frames": end - start + 1, "end_reason": "split", "judged": judged}
        s["judge_frames"] = m.judge_frames(s) if judged else []
        return s

    def judgments(self, states):
        return {f: {"state": st, "object": None} for f, st in zip([65, 92, 122], states)}

    def test_two_of_three_vote(self):
        ap = np.full(280, HELD)
        s = m.fuse_segment(self.seg(), self.judgments(["held", "held", "empty"]), ap, VC)
        self.assertEqual((s["state"], s["decided_by"], s["votes"]), ("held", "vote", {"held": 2, "empty": 1, "uncertain": 0}))
        s = m.fuse_segment(self.seg(), self.judgments(["empty", "uncertain", "empty"]), ap, VC)
        self.assertEqual((s["state"], s["decided_by"]), ("empty", "vote"))   # the VLM overrides a held-like aperture
        s = m.fuse_segment(self.seg(), self.judgments(["held", "held", "held"]), np.full(280, CLOSED), VC)
        self.assertEqual((s["state"], s["decided_by"]), ("held", "vote"))   # ... and a closed-like aperture

    def test_fallback_to_median_aperture(self):
        split = self.judgments(["held", "empty", "uncertain"])
        for ap_value, want in [(HELD, "held"), (0.006, "held"), (0.039, "held"), (CLOSED, "empty"), (0.0059, "empty"), (0.0391, "empty")]:
            s = m.fuse_segment(self.seg(), split, np.full(280, ap_value), VC)
            self.assertEqual((s["state"], s["decided_by"]), (want, "telemetry"), ap_value)
        # only uncertain answers also fall back
        s = m.fuse_segment(self.seg(), self.judgments(["uncertain"] * 3), np.full(280, HELD), VC)
        self.assertEqual((s["state"], s["decided_by"]), ("held", "telemetry"))

    def test_unjudged_segment_is_uncertain(self):
        s = m.fuse_segment(self.seg(judged=False), {}, np.full(280, HELD), VC)
        self.assertEqual((s["state"], s["decided_by"], s["votes"]), ("uncertain", "over_budget", {"held": 0, "empty": 0, "uncertain": 0}))

    def test_malformed_answer_counts_as_uncertain_and_held_obs_modes(self):
        ep = drop_ep(28)
        with tempfile.TemporaryDirectory() as tmp:
            backend = Backend(ep, states={65: "garbage", 92: "empty"})
            pred = run(ep, backend, tmp)
            res = result_of(tmp)
        self.assertEqual(backend.state_frames, [65, 92, 122, 129, 202, 277])
        judg = {j["frame"]: j["state"] for j in res["evidence"]["judgments"]}
        self.assertEqual(judg, {65: "uncertain", 92: "empty", 122: "held", 129: "empty", 202: "empty", 277: "empty"})
        cands = res["evidence"]["candidates"]
        self.assertEqual((cands[0]["state"], cands[0]["decided_by"]), ("held", "telemetry"))  # 1-1-1 -> median 2 cm
        self.assertEqual((cands[1]["state"], cands[1]["decided_by"]), ("empty", "vote"))
        states = [o["state"] for o in pred["held_obs"]]
        self.assertEqual((states[65], states[92], states[122], states[66]), ("uncertain", "empty", "held", "held"))  # judged frames: VLM verdict
        self.assertEqual(event_tuples(pred), [("grasp", 60, 61), ("drop", 124, 125)])
        cfg = json.loads(json.dumps(m.CONFIG))
        cfg["verify"]["held_obs_judged_frames"] = "segment"
        with tempfile.TemporaryDirectory() as tmp:
            pred2 = run(ep, Backend(ep, states={65: "garbage", 92: "empty"}), tmp, cfg)
        states2 = [o["state"] for o in pred2["held_obs"]]
        self.assertEqual(states2[61:125], ["held"] * 64)
        self.assertEqual(states2[125:], ["empty"] * 155)

    def test_frame_states_layout(self):
        segs = [{"start": 4, "end": 9, "state": "held"}, {"start": 10, "end": 14, "state": "empty"}, {"start": 20, "end": 23, "state": "uncertain"}]
        st = m.frame_states(26, segs, {6: {"state": "empty"}, 21: {"state": "held"}})
        self.assertEqual(st, ["empty"] * 4 + ["held", "held", "empty", "held", "held", "held"] + ["empty"] * 10 + ["uncertain", "held", "uncertain", "uncertain", "empty", "empty"])
        st = m.frame_states(26, segs, {6: {"state": "empty"}}, judged_mode="segment")
        self.assertEqual(st[6], "held")


# ------------------------------------------------------------------ 3. events
class EventTests(unittest.TestCase):
    def test_drop_at_split(self):
        ep = drop_ep(28)
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(ep, Backend(ep), tmp)
            res = result_of(tmp)
        self.assertEqual(event_tuples(pred), [("grasp", 60, 61), ("drop", 124, 125)])
        self.assertEqual([e["chunk"] for e in pred["events"]], [6, 12])
        self.assertEqual([e["object"] for e in pred["events"]], ["alphabet_soup_1"] * 2)
        self.assertEqual(pred["held_object"], "alphabet_soup_1")
        self.assertEqual(res["evidence"]["held_segments"], [{"start": 61, "end": 124, "end_reason": "split", "members": [0], "n_frames": 64}])
        # completion layer (event_first_v2 rules) on top of the fused events
        self.assertEqual((pred["decisive_chunk"], pred["cause"]), (12, "grasp"))
        self.assertEqual(pred["chunk_labels"][12], "failure_inducing")
        self.assertEqual(pred["completion_rules"][12], "1_drop")
        self.assertEqual(pred["chunk_labels"][:6], ["progress"] * 6)
        self.assertEqual(pred["chunk_labels"][13:], ["neutral"] * 15)
        self.assertNotIn(None, pred["chunk_labels"])
        self.assertEqual(len(pred["chunk_labels"]), 28)

    def test_release_when_the_command_opens(self):
        ep = Ep(28, close=[(57, 122)], held=[(61, 122)], moving=[(0, 125)])
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(ep, Backend(ep), tmp)
        self.assertEqual(event_tuples(pred), [("grasp", 60, 61), ("release", 122, 123)])
        self.assertEqual((pred["decisive_chunk"], pred["cause"]), (12, "manipulation"))
        self.assertEqual(pred["completion_rules"][12], "2_release_last")
        states = [o["state"] for o in pred["held_obs"]]
        self.assertEqual(states[57:61], ["empty"] * 4)
        self.assertEqual(states[61:123], ["held"] * 62)
        self.assertEqual(states[123:], ["empty"] * 157)

    def test_no_end_event_when_held_to_the_last_frame(self):
        ep = Ep(28, close=[(57, 279)], held=[(61, 279)], moving=[(0, 200)])
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(ep, Backend(ep), tmp)
        self.assertEqual(event_tuples(pred), [("grasp", 60, 61)])
        self.assertEqual(pred["cause"], "manipulation")
        self.assertEqual(pred["decisive_chunk"], 20)  # 6s_stall_decisive (motion stops at 200)

    def test_vlm_empty_overrides_a_held_like_aperture(self):
        ep = drop_ep(28, held=[])
        with tempfile.TemporaryDirectory() as tmp:
            backend = Backend(ep)
            pred = run(ep, backend, tmp)
            res = result_of(tmp)
        self.assertEqual(pred["events"], [])
        self.assertIsNone(pred["held_object"])
        self.assertEqual(backend.generate_calls, 0)  # no identification without a held segment
        self.assertEqual([c["state"] for c in res["evidence"]["candidates"]], ["empty", "empty"])
        self.assertTrue(all(o["state"] == "empty" for o in pred["held_obs"]))
        self.assertEqual((pred["decisive_chunk"], pred["cause"]), (12, "grasp"))  # close-on-nothing onset at 125 (rule 3)

    def test_adjacent_held_segments_are_merged(self):
        ep = drop_ep(28, held=[(61, 279)])  # the VLM sees the (thin) object held on the post-split segment too
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(ep, Backend(ep), tmp)
            res = result_of(tmp)
        self.assertEqual(res["evidence"]["held_segments"], [{"start": 61, "end": 279, "end_reason": "episode_end", "members": [0, 1], "n_frames": 219}])
        self.assertEqual(event_tuples(pred), [("grasp", 60, 61)])

    def test_merge_gap_rule(self):
        def seg(i, a, b, reason="open", state="held"):
            return {"index": i, "start": a, "end": b, "end_reason": reason, "state": state}
        merged = m.merge_held_segments([seg(0, 10, 20, "split"), seg(1, 24, 30), seg(2, 35, 40, "episode_end"), seg(3, 50, 60, state="empty")], 4)
        self.assertEqual([(h["start"], h["end"], h["end_reason"], h["members"]) for h in merged], [(10, 30, "open", [0, 1]), (35, 40, "episode_end", [2])])
        merged = m.merge_held_segments([seg(0, 10, 20, "split"), seg(1, 25, 30)], 4)  # gap of exactly 4 frames stays separate
        self.assertEqual(len(merged), 2)

    def test_two_holds_and_chunk_mapping(self):
        ep = Ep(28, close=[(57, 122), (140, 279)], held=[(61, 122), (144, 279)], moving=[(0, 125), (130, 200)])
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(ep, Backend(ep), tmp)
        self.assertEqual(event_tuples(pred), [("grasp", 60, 61), ("release", 122, 123), ("grasp", 143, 144)])
        self.assertEqual([e["chunk"] for e in pred["events"]], [6, 12, 14])
        self.assertEqual(pred["completion_rules"][14], "4_regrasp")
        # non-uniform chunk layout: the event chunk follows ep.chunk_of_frame(last_before)
        ep7 = drop_ep(40, moving=[(0, 125)])
        ep7.chunks = [(c * 7, (c + 1) * 7) for c in range(40)]
        with tempfile.TemporaryDirectory() as tmp:
            pred7 = run(ep7, Backend(ep7), tmp)
        self.assertEqual([e["chunk"] for e in pred7["events"]], [60 // 7, 124 // 7])
        self.assertEqual(len(pred7["chunk_labels"]), 40)

    def test_events_from_held_segments_helper(self):
        ep = Ep(13)
        held = [{"start": 0, "end": 9, "end_reason": "open"}, {"start": 30, "end": 40, "end_reason": "split"}, {"start": 50, "end": 129, "end_reason": "episode_end"}]
        ev = m.events_from_held_segments(ep, held, "x")
        self.assertEqual([(e["type"], e["last_before"], e["first_after"], e["chunk"]) for e in ev],
                         [("release", 9, 10, 0), ("grasp", 29, 30, 2), ("drop", 40, 41, 4), ("grasp", 49, 50, 4)])
        self.assertTrue(all(e["object"] == "x" for e in ev))


# ------------------------------------------------------------------ 4. identification, contract, cache, privacy
class ContractTests(unittest.TestCase):
    def test_contract_on_28_and_52_chunks(self):
        for n_chunks in (28, 52):
            with self.subTest(n_chunks=n_chunks):
                ep = drop_ep(n_chunks)
                with tempfile.TemporaryDirectory() as tmp:
                    pred = run(ep, Backend(ep), tmp)
                    res = result_of(tmp)
                self.assertTrue(CONTRACT_KEYS.issubset(pred))
                self.assertEqual(len(pred["chunk_labels"]), n_chunks)
                self.assertEqual(len(pred["chunk_q"]), n_chunks)
                self.assertEqual([o["frame"] for o in pred["held_obs"]], list(range(ep.n)))
                self.assertTrue(all(o["state"] in ("held", "empty", "uncertain") and o["object"] is None for o in pred["held_obs"]))
                self.assertTrue(all(0 <= f < ep.n for f in ep.frames_seen))
                self.assertTrue(all(lab in ("progress", "failure_inducing", "recovery", "neutral", "aftermath") for lab in pred["chunk_labels"]))
                self.assertTrue(all(q > 0.0 for q in pred["chunk_q"]))
                self.assertEqual((pred["decisive_chunk"], pred["cause"]), (12, "grasp"))
                self.assertEqual(pred["raw_dir"], str(Path(tmp) / "fused_v4"))
                self.assertEqual(pred["peak_mem_gb"], 3.0)
                for key in ("candidates", "judgments", "held_segments", "events", "identify", "close_runs"):
                    self.assertIn(key, res["evidence"])
                self.assertEqual(res["config"]["family"], "fused_cmd_vlm")
                self.assertEqual(res["prediction"]["events"], pred["events"])

    def test_call_budget_and_identify_frames(self):
        ep = drop_ep(28)
        with tempfile.TemporaryDirectory() as tmp:
            backend = Backend(ep)
            pred = run(ep, backend, tmp)
            res = result_of(tmp)
        self.assertEqual(backend.generate_many_calls, 1)       # all verification frames in one call
        self.assertEqual(backend.generate_many_prompts, 6)     # 2 candidates x 3 frames
        self.assertEqual(backend.generate_calls, 4)            # identification, one wrist close-up per call
        self.assertEqual((pred["n_model_calls"], pred["n_prompts"]), (5, 10))
        id_frames = [r["frame"] for r in res["evidence"]["identify"]]
        self.assertEqual(len(id_frames), 4)
        self.assertTrue(all(77 <= f <= 108 for f in id_frames), id_frames)  # middle half of 61..124
        self.assertEqual(res["evidence"]["identify_frames"], id_frames)
        self.assertEqual(m.identify_frames([{"start": 0, "end": 7, "n_frames": 8}]), [2, 3, 4, 5])
        self.assertEqual(sorted(set(backend.systems)), sorted({STATE_SYSTEM, backend.systems[-1]}))

    def test_no_candidates_means_no_calls(self):
        ep = Ep(13, moving=[(0, 80)])
        with tempfile.TemporaryDirectory() as tmp:
            backend = Backend(ep)
            pred = run(ep, backend, tmp)
        self.assertEqual((backend.generate_calls, backend.generate_many_calls, pred["n_model_calls"]), (0, 0, 0))
        self.assertEqual(pred["events"], [])
        self.assertIsNone(pred["held_object"])
        self.assertTrue(all(o["state"] == "empty" for o in pred["held_obs"]))
        self.assertEqual(len(pred["held_obs"]), 130)
        self.assertIsNone(pred["decisive_chunk"])
        self.assertEqual(pred["cause"], "reaching")  # never held, no evidence -> reaching (completion flag)

    def test_cache_hit_makes_no_call(self):
        ep = drop_ep(28)
        with tempfile.TemporaryDirectory() as tmp:
            first = run(ep, Backend(ep), tmp)
            cached = sorted(p.parent.name for p in (Path(tmp) / "fused_v4").glob("*/*.json"))
            self.assertEqual(cached, ["identify"] * 4 + ["verify"] * 6)
            again = Backend(ep)
            second = run(ep, again, tmp)
        self.assertEqual((again.generate_calls, again.generate_many_calls, second["n_model_calls"]), (0, 0, 0))
        for key in ("held_obs", "events", "held_object", "chunk_labels", "chunk_q", "decisive_chunk", "cause", "completion_rules"):
            self.assertEqual(first[key], second[key])

    def test_privileged_columns_are_never_read(self):
        ep = drop_ep(13, moving=[(0, 100)])
        with self.assertRaises(AssertionError):
            ep.col("priv.obj_grasped")  # the guard is live
        ep.accessed = []
        with tempfile.TemporaryDirectory() as tmp:
            run(ep, Backend(ep), tmp)
        self.assertEqual(ep.accessed, [])

    def test_config(self):
        cfg = m.CONFIG
        json.dumps(cfg)
        self.assertEqual({k: v for k, v in cfg["completion"].items() if k != "never_held_cause_reaching"}, v2.CONFIG["completion"])
        self.assertTrue(cfg["completion"]["never_held_cause_reaching"])
        for k in ("max_frames", "scale", "temperature"):
            self.assertEqual(cfg["identify"][k], v2.CONFIG["identify"][k])
        self.assertEqual((cfg["candidates"]["close_min_run"], cfg["candidates"]["trim_start"], cfg["candidates"]["max_judged"]), (8, 4, 6))
        self.assertEqual((cfg["candidates"]["split_from_m"], cfg["candidates"]["split_collapse_to_m"], cfg["candidates"]["split_stay_frames"]), (0.006, 0.003, 6))
        self.assertEqual((cfg["verify"]["vote_min"], cfg["verify"]["scale"], cfg["verify"]["camera"], cfg["verify"]["temperature"]), (2, 2.0, "both", 0.0))
        self.assertEqual((cfg["verify"]["fallback_held_lo_m"], cfg["verify"]["fallback_held_hi_m"]), (0.006, 0.039))
        self.assertEqual(cfg["events"]["merge_gap_frames"], 4)
        self.assertEqual(cfg["chunk_passes"], [])
        self.assertFalse(cfg["run_chunk_passes"])
        self.assertIsNot(cfg["completion"], v2.CONFIG["completion"])  # copies, the v2 config is not shared
        from methods import REGISTRY, load_method
        self.assertEqual(REGISTRY["fused_v4"], "methods.fused_v4")
        self.assertTrue(callable(load_method("fused_v4").run))


if __name__ == "__main__":
    unittest.main()
