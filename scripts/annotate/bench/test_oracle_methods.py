"""CPU checks for the ORACLE-CONDITIONED ablation methods (fake backend, stub episode with telemetry, stub reference
dict written to a temporary references directory; no model, no dataset).

Run (WSL): python -m unittest discover -s scripts/annotate/bench -p test_oracle_methods.py
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE / "methods", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _oracle_lib as olib  # noqa: E402
import oracle_chunk  # noqa: E402
import oracle_moment  # noqa: E402
import oracle_rules  # noqa: E402
import oracle_whole  # noqa: E402
import prompt  # noqa: E402
from combine_local_evidence import consensus_frames, transitions  # noqa: E402
from local_segmenter import SYSTEM as CHUNK_SYSTEM  # noqa: E402
from methods import load_method  # noqa: E402
from test_event_first_methods import CONTRACT_KEYS  # noqa: E402
from test_event_first_v2 import Ep, V2Backend  # noqa: E402

FI, PR, NE, RE, AF = "failure_inducing", "progress", "neutral", "recovery", "aftermath"
METHODS = (oracle_rules, oracle_whole, oracle_chunk, oracle_moment)


# ------------------------------------------------------------------ stubs
def drop_episode(n_chunks=28):
    """approach 0-59 (moving), grasp 59->60, held 60..124, drop 124->125 with the command still CLOSE, idle tail."""
    return Ep(n_chunks, held_runs=[(60, 124)], cmd=[(57, 1.0)], moving=[(0, 125)])


def drop_reference(n_chunks=28):
    """Reference matching drop_episode: bowl-style drop_transport with alphabet_soup_1 held frames 60..124."""
    n = n_chunks * 10
    return {
        "reference_version": "r2", "dataset": "stub", "episode_index": 0, "task": "put the alphabet soup in the basket", "success": False,
        "n_frames": n, "fps": 20, "n_chunks": n_chunks, "chunks": [[c * 10, (c + 1) * 10] for c in range(n_chunks)],
        "object_slots": ["alphabet_soup_1", "cream_cheese_1", "basket_1"], "target_slot": "alphabet_soup_1", "goal_slot": "basket_1", "fixtures": [],
        "held_runs": [
            {"start": 0, "end": 57, "state": "empty", "object": None},
            {"start": 58, "end": 59, "state": "ambiguous", "object": "alphabet_soup_1"},
            {"start": 60, "end": 124, "state": "held", "object": "alphabet_soup_1"},
            {"start": 125, "end": 126, "state": "ambiguous", "object": "alphabet_soup_1"},
            {"start": 127, "end": n - 1, "state": "empty", "object": None},
        ],
        "events": [
            {"index": 60, "type": "grasp", "object": "alphabet_soup_1", "last_before": 59, "first_after": 60, "chunk": 5, "gripper_cmd_open": False, "hold_frames": 65},
            {"index": 125, "type": "drop", "object": "alphabet_soup_1", "last_before": 124, "first_after": 125, "chunk": 12, "gripper_cmd_open": False, "hold_frames": 65},
        ],
        "wrong_object_contacts": [], "collisions": [], "fixture_motion": [],
        "failure_mode": "drop_transport", "cause": "grasp", "decisive_chunk": 12,
        "chunk_labels": [{"chunk": c, "allowed": [PR], "primary": PR, "rule": "pre_advance"} for c in range(12)]
                        + [{"chunk": 12, "allowed": [FI], "primary": FI, "rule": "decisive"}]
                        + [{"chunk": c, "allowed": [AF, NE], "primary": AF, "rule": "post"} for c in range(13, n_chunks)],
    }


def held_at_end_reference(n_chunks=28):
    """hold_no_release with the arm still moving: grasp only, decisive null."""
    ref = drop_reference(n_chunks)
    n = n_chunks * 10
    ref.update({"held_runs": [{"start": 0, "end": 57, "state": "empty", "object": None},
                              {"start": 58, "end": 59, "state": "ambiguous", "object": "alphabet_soup_1"},
                              {"start": 60, "end": n - 3, "state": "held", "object": "alphabet_soup_1"},
                              {"start": n - 2, "end": n - 1, "state": "ambiguous", "object": "alphabet_soup_1"}],
                "events": ref["events"][:1], "failure_mode": "hold_no_release", "cause": "manipulation", "decisive_chunk": None})
    return ref


def never_held_reference(n_chunks=13):
    ref = drop_reference(n_chunks)
    ref.update({"held_runs": [{"start": 0, "end": n_chunks * 10 - 1, "state": "empty", "object": None}], "events": [],
                "failure_mode": "never_reached", "cause": "reaching", "decisive_chunk": None})
    return ref


def wrong_object_reference(n_chunks=28):
    ref = drop_reference(n_chunks)
    for r in ref["held_runs"]:
        if r["object"]:
            r["object"] = "cream_cheese_1"
    for e in ref["events"]:
        e["object"] = "cream_cheese_1"
    ref.update({"failure_mode": "wrong_object", "cause": "sequencing_semantic", "decisive_chunk": 5})
    return ref


def annotation_json(cause="grasp", decisive=12, fi_chunk=12, n_chunks=28, tail=AF):
    segs = [{"start": 0, "end": fi_chunk - 1, "label": PR, "confidence": 0.9},
            {"start": fi_chunk, "end": fi_chunk, "label": FI, "cause": cause, "confidence": 0.8},
            {"start": fi_chunk + 1, "end": n_chunks - 1, "label": tail, "confidence": 0.7}]
    return json.dumps({"outcome": "failure", "failure_symptom": "the can slips out", "root_cause": "off-centre grasp", "cause": cause,
                       "failure_onset": decisive - 1, "decisive_error": decisive, "visible_failure": decisive + 1, "recoverable_until": decisive + 2,
                       "segments": segs})


def moment_json(chunk=12, cause="grasp", sentence="closed the gripper 3 cm left of the can", confidence=0.8):
    return json.dumps({"decisive_chunk": chunk, "cause": cause, "what_happened": sentence, "confidence": confidence})


class OracleBackend(V2Backend):
    """V2Backend (per-chunk answers) plus canned whole-episode and moment answers, cycled per sample."""

    def __init__(self, ep, whole=None, moment=None, **kw):
        super().__init__(ep, **kw)
        self.whole = list(whole or [annotation_json()])
        self.moment = list(moment or [moment_json()])
        self.whole_calls = self.moment_calls = 0
        self.whole_texts, self.moment_texts = [], []

    def _answer(self, system, content):
        text = "\n".join(b["text"] for b in content if b["type"] == "text")
        if system == prompt.SYSTEM:
            self.whole_texts.append(text)
            i, self.whole_calls = self.whole_calls, self.whole_calls + 1
            return self.whole[i % len(self.whole)]
        if system == oracle_moment.MOMENT_SYSTEM:
            self.moment_texts.append(text)
            i, self.moment_calls = self.moment_calls, self.moment_calls + 1
            return self.moment[i % len(self.moment)]
        return super()._answer(system, content)


def write_reference(tmp, ep, ref):
    refs = Path(tmp) / "references"
    path = refs / ep.name / f"episode_{ep.ep:06d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ref))
    return refs


def run(method, ep, backend, tmp, ref, via_file=True):
    """Run a method against a stub reference either through a temporary references dir (the real path) or injected."""
    if via_file:
        return method.run(ep, backend, Path(tmp) / method.__name__, ref_dir=write_reference(tmp, ep, ref))
    return method.run(ep, backend, Path(tmp) / method.__name__, reference=ref)


# ------------------------------------------------------------------ tests
class LibTests(unittest.TestCase):
    def test_oracle_facts_and_held_object(self):
        facts = olib.oracle_facts(drop_reference())
        self.assertEqual([(e["type"], e["last_before"], e["first_after"], e["chunk"], e["object"]) for e in facts["events"]],
                         [("grasp", 59, 60, 5, "alphabet_soup_1"), ("drop", 124, 125, 12, "alphabet_soup_1")])
        self.assertEqual(facts["held_object"], "alphabet_soup_1")
        self.assertIsNone(olib.oracle_facts(never_held_reference())["held_object"])
        # longest held run wins
        ref = drop_reference()
        ref["held_runs"] = [{"start": 0, "end": 4, "state": "held", "object": "cream_cheese_1"}] + ref["held_runs"][1:]
        self.assertEqual(olib.oracle_facts(ref)["held_object"], "alphabet_soup_1")
        self.assertEqual(olib.longest_held_object([]), None)

    def test_facts_text(self):
        ep = drop_episode()
        text = olib.facts_text(drop_reference(), ep)
        self.assertIn("Verified events: grasp of alphabet soup 1 in chunk 5 (steps 59-60); drop in chunk 12 (steps 124-125).", text)
        self.assertIn("The gripper never holds anything after chunk 12.", text)
        self.assertIn("Object held: alphabet_soup_1 (the target).", text)
        text = olib.facts_text(wrong_object_reference(), ep)
        self.assertIn("grasp of cream cheese 1 in chunk 5", text)
        self.assertIn("Object held: cream_cheese_1 (NOT the target).", text)
        text = olib.facts_text(held_at_end_reference(), ep)
        self.assertIn("holds alphabet soup 1 from chunk 5 to the end of the episode (chunk 27).", text)
        text = olib.facts_text(never_held_reference(13), Ep(13))
        self.assertIn("Verified events: none. The gripper never holds any object", text)
        self.assertIn("Object held: none.", text)
        self.assertNotIn("\n", text)

    def test_reference_states_rows(self):
        rows = olib.reference_states_rows(drop_reference(), 280)
        self.assertEqual(len(rows), 1)
        states = rows[0]["parsed"]["states"]
        self.assertEqual(len(states), 280)
        self.assertEqual([s["frame"] for s in states], list(range(280)))
        by = {s["frame"]: s["state"] for s in states}
        self.assertEqual((by[0], by[57], by[58], by[59], by[60], by[124], by[125], by[126], by[127], by[279]),
                         ("empty", "empty", "uncertain", "uncertain", "held", "held", "uncertain", "uncertain", "empty", "empty"))
        # the consensus/transitions chain reproduces the reference events from these rows
        ev = transitions(consensus_frames(rows))
        self.assertEqual([(e["event"], e["last_before_frame"], e["first_after_frame"]) for e in ev], [("grasp", 57, 60), ("loss_or_release", 124, 127)])
        # truncation and uncovered frames
        short = olib.reference_states_rows(drop_reference(), 100)[0]["parsed"]["states"]
        self.assertEqual(len(short), 100)
        gap = olib.reference_states_rows({"held_runs": [{"start": 0, "end": 4, "state": "empty"}]}, 8)[0]["parsed"]["states"]
        self.assertEqual([s["state"] for s in gap], ["empty"] * 5 + ["uncertain"] * 3)

    def test_base_prediction(self):
        ep = drop_episode()
        pred = olib.base_prediction(ep, olib.oracle_facts(drop_reference()))
        self.assertEqual(pred["held_obs"], [])
        self.assertEqual(pred["held_object"], "alphabet_soup_1")
        self.assertEqual([e["chunk"] for e in pred["events"]], [5, 12])
        self.assertEqual(pred["chunk_labels"], [None] * 28)
        self.assertEqual(pred["chunk_q"], [0.0] * 28)
        self.assertIsNone(pred["decisive_chunk"])
        self.assertIsNone(pred["cause"])

    def test_load_reference_missing_and_chunk_mismatch(self):
        ep = drop_episode()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                olib.load_reference(ep, Path(tmp))
            refs = write_reference(tmp, ep, drop_reference(13))
            with self.assertRaises(ValueError):
                olib.load_reference(ep, refs)
            refs = write_reference(tmp, ep, drop_reference(28))
            self.assertEqual(olib.load_reference(ep, refs)["decisive_chunk"], 12)
        self.assertEqual(olib.reference_path(ep).name, "episode_000000.json")
        self.assertEqual(olib.reference_path(ep).parent.name, "stub")
        self.assertEqual(olib.reference_path(ep).parents[1].name, "references")


class ConfigTests(unittest.TestCase):
    def test_all_configs_marked_oracle_conditioned(self):
        for m in METHODS:
            with self.subTest(method=m.__name__):
                self.assertIs(m.CONFIG["oracle_conditioned"], True)
                self.assertEqual(m.CONFIG["family"], "oracle_conditioned")
                self.assertIn("reference", m.CONFIG["note"])
                self.assertIn("ablation", m.CONFIG["note"].lower())
                self.assertIn("never a production annotator", m.CONFIG["note"])
                json.dumps(m.CONFIG)
        for m in (oracle_rules, oracle_chunk, oracle_moment):
            self.assertTrue(m.CONFIG["completion"]["never_held_cause_reaching"])
        import event_first_v2 as v2
        self.assertNotIn("never_held_cause_reaching", v2.CONFIG["completion"])  # v2's config is not mutated
        self.assertEqual((oracle_whole.CONFIG["k"], oracle_whole.CONFIG["temperature"], oracle_whole.CONFIG["max_new_tokens"], oracle_whole.CONFIG["batch"]), (5, 0.7, 1200, 3))
        self.assertEqual((oracle_chunk.CONFIG["chunk"]["k"], oracle_chunk.CONFIG["chunk"]["seed"], oracle_chunk.CONFIG["chunk"]["context"]), (3, 7100, 0))
        self.assertEqual((oracle_moment.CONFIG["k"], oracle_moment.CONFIG["temperature"]), (5, 0.5))

    def test_registry(self):
        for name in ("oracle_rules", "oracle_whole", "oracle_chunk", "oracle_moment"):
            mod = load_method(name)
            self.assertTrue(callable(mod.run))
            self.assertIs(mod.CONFIG["oracle_conditioned"], True)


class OracleRulesTests(unittest.TestCase):
    def test_drop_episode_reads_reference_and_has_no_nulls(self):
        ep = drop_episode()
        with tempfile.TemporaryDirectory() as tmp:
            backend = OracleBackend(ep)
            pred = run(oracle_rules, ep, backend, tmp, drop_reference())
            result = json.loads((Path(tmp) / "oracle_rules" / "result.json").read_text())
        self.assertEqual((backend.generate_calls, backend.generate_many_calls, pred["n_model_calls"]), (0, 0, 0))
        self.assertTrue(CONTRACT_KEYS.issubset(pred))
        self.assertEqual([(e["type"], e["last_before"], e["first_after"], e["object"]) for e in pred["events"]],
                         [("grasp", 59, 60, "alphabet_soup_1"), ("drop", 124, 125, "alphabet_soup_1")])
        self.assertEqual(pred["held_object"], "alphabet_soup_1")
        self.assertEqual(pred["held_obs"], [])
        self.assertNotIn(None, pred["chunk_labels"])
        self.assertEqual(pred["chunk_labels"][:5], [PR] * 5)
        self.assertEqual(pred["chunk_labels"][5:12], [PR] * 7)
        self.assertEqual((pred["chunk_labels"][12], pred["completion_rules"][12]), (FI, "1_drop"))
        self.assertEqual(pred["chunk_labels"][13:], [NE] * 15)
        self.assertEqual((pred["decisive_chunk"], pred["cause"]), (12, "grasp"))
        self.assertTrue(all(q > 0 for q in pred["chunk_q"]))
        self.assertIs(pred["oracle_conditioned"], True)
        self.assertIs(result["config"]["oracle_conditioned"], True)
        self.assertTrue(result["evidence"]["reference"]["source"].endswith("stub/episode_000000.json"))
        self.assertEqual(result["evidence"]["facts"]["held_object"], "alphabet_soup_1")
        self.assertIn("Verified events", result["evidence"]["facts_text"])
        self.assertEqual(result["prediction"]["chunk_labels"], pred["chunk_labels"])

    def test_reference_file_is_what_is_read(self):
        # the same episode with a wrong-object reference flips the branch: the method reads the file, not the telemetry alone
        ep = drop_episode()
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(oracle_rules, ep, OracleBackend(ep), tmp, wrong_object_reference())
        self.assertEqual(pred["held_object"], "cream_cheese_1")
        self.assertEqual(pred["chunk_labels"][:5], [FI] * 5)
        self.assertEqual((pred["chunk_labels"][5], pred["completion_rules"][5]), (FI, "W_wrong_grasp"))
        self.assertEqual((pred["decisive_chunk"], pred["cause"]), (5, "sequencing_semantic"))
        self.assertNotIn(None, pred["chunk_labels"])

    def test_never_held_gives_reaching_and_labels(self):
        ep = Ep(13, held_runs=[], cmd=[], moving=[(0, 80)])
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(oracle_rules, ep, OracleBackend(ep), tmp, never_held_reference(13), via_file=False)
        self.assertEqual(pred["events"], [])
        self.assertIsNone(pred["held_object"])
        self.assertNotIn(None, pred["chunk_labels"])
        self.assertEqual(pred["chunk_labels"][:8], [PR] * 8)
        self.assertEqual(pred["chunk_labels"][8:], [NE] * 5)
        self.assertEqual(set(pred["completion_rules"]), {"10_motion"})
        self.assertIsNone(pred["decisive_chunk"])
        self.assertEqual(pred["cause"], "reaching")

    def test_missing_reference_raises(self):
        ep = drop_episode()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                oracle_rules.run(ep, OracleBackend(ep), Path(tmp) / "w", ref_dir=Path(tmp) / "nowhere")


class OracleWholeTests(unittest.TestCase):
    def test_mapping_from_canned_annotation(self):
        ep = drop_episode()
        with tempfile.TemporaryDirectory() as tmp:
            backend = OracleBackend(ep, whole=[annotation_json()])
            pred = run(oracle_whole, ep, backend, tmp, drop_reference())
            result = json.loads((Path(tmp) / "oracle_whole" / "result.json").read_text())
            cached = [json.loads(p.read_text()) for p in (Path(tmp) / "oracle_whole" / "whole").glob("*.json")]
        self.assertEqual((backend.generate_calls, backend.whole_calls, pred["n_model_calls"]), (1, 5, 1))
        self.assertEqual(pred["chunk_labels"], [PR] * 12 + [FI] + [AF] * 15)
        self.assertEqual(pred["chunk_q"], [1.0] * 28)
        self.assertEqual((pred["decisive_chunk"], pred["cause"]), (12, "grasp"))
        # events and held object are the oracle's, untouched by the VLM
        self.assertEqual([e["type"] for e in pred["events"]], ["grasp", "drop"])
        self.assertEqual(pred["held_object"], "alphabet_soup_1")
        self.assertEqual(result["evidence"]["n_parsed"], 5)
        self.assertEqual(result["evidence"]["aggregate"]["cause_votes"], {"grasp": 5})
        self.assertEqual(len(cached), 1)
        self.assertEqual(len(cached[0]["raws"]), 5)
        # the prompt carries the verified facts, the glossary, the signal table, and not the tentative suffix
        text = backend.whole_texts[0]
        self.assertIn("Verified events: grasp of alphabet soup 1 in chunk 5", text)
        self.assertIn("Object held: alphabet_soup_1 (the target)", text)
        self.assertIn("verified against the simulator state", text)
        self.assertNotIn("tentative visual observations", text)
        self.assertIn("alphabet soup = a short DARK BLUE can", text)
        self.assertIn("gripper_cmd", text)
        self.assertIn("Episode outcome: FAILURE", text)

    def test_mixed_votes_and_garbage(self):
        ep = drop_episode()
        a = annotation_json()
        b = annotation_json(cause="manipulation", decisive=13, fi_chunk=13)
        with tempfile.TemporaryDirectory() as tmp:
            backend = OracleBackend(ep, whole=[a, a, b, "no json here", a])
            pred = run(oracle_whole, ep, backend, tmp, drop_reference(), via_file=False)
            result = json.loads((Path(tmp) / "oracle_whole" / "result.json").read_text())
        self.assertEqual(result["evidence"]["n_parsed"], 4)
        self.assertEqual(len(result["evidence"]["parse_errors"]), 1)
        self.assertEqual(pred["cause"], "grasp")                       # 3 of 5 attempted
        self.assertEqual(pred["decisive_chunk"], 12)                   # median of 12,12,13,12
        self.assertEqual(pred["chunk_labels"][12], FI)
        self.assertEqual(pred["chunk_q"][12], 0.6)                     # 3 failure_inducing vs 1 progress (b) of 5 attempted
        self.assertEqual(pred["chunk_labels"][13], AF)                 # 3 aftermath vs 1 failure_inducing
        self.assertEqual(pred["chunk_q"][13], 0.6)
        self.assertEqual(pred["chunk_labels"][0], PR)

    def test_no_majority_and_unclear_cause_and_all_garbage(self):
        ep = drop_episode()
        c1 = annotation_json(cause="grasp", decisive=12)
        c2 = annotation_json(cause="manipulation", decisive=14, fi_chunk=14)
        c3 = annotation_json(cause="collision", decisive=10, fi_chunk=10)
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(oracle_whole, ep, OracleBackend(ep, whole=[c1, c2, c3, "x", "y"]), tmp, drop_reference(), via_file=False)
        self.assertEqual(pred["cause"], "unclear")                    # 1/1/1 cause votes: no strict majority over 5 attempts
        self.assertEqual(pred["decisive_chunk"], 12)                  # 3 of 5 samples gave a value (3*2 > 5): median of 12, 14, 10
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(oracle_whole, ep, OracleBackend(ep, whole=["garbage"]), tmp, drop_reference(), via_file=False)
            result = json.loads((Path(tmp) / "oracle_whole" / "result.json").read_text())
        self.assertEqual(pred["chunk_labels"], [None] * 28)
        self.assertEqual(pred["chunk_q"], [0.0] * 28)
        self.assertIsNone(pred["decisive_chunk"])
        self.assertIsNone(pred["cause"])
        self.assertIsNone(result["evidence"]["aggregate"])
        self.assertEqual(pred["held_object"], "alphabet_soup_1")      # oracle fields survive a VLM failure

    def test_map_aggregate_filters_labels(self):
        agg = {"chunk_label": [PR, "uncertain", "weird", FI], "chunk_q": [1.0, 0.0, 0.2, 0.6],
               "landmarks": {"decisive_error": {"value": None}}, "cause": "unclear"}
        labels, q, decisive, cause = oracle_whole.map_aggregate(agg, 5)
        self.assertEqual(labels, [PR, None, None, FI, None])
        self.assertEqual(q, [1.0, 0.0, 0.2, 0.6, 0.0])
        self.assertIsNone(decisive)
        self.assertEqual(cause, "unclear")

    def test_cache_hit(self):
        ep = drop_episode()
        with tempfile.TemporaryDirectory() as tmp:
            first = run(oracle_whole, ep, OracleBackend(ep), tmp, drop_reference(), via_file=False)
            again = OracleBackend(ep)
            second = run(oracle_whole, ep, again, tmp, drop_reference(), via_file=False)
        self.assertEqual((again.generate_calls, second["n_model_calls"]), (0, 0))
        for key in ("events", "held_object", "chunk_labels", "chunk_q", "decisive_chunk", "cause"):
            self.assertEqual(first[key], second[key])


class OracleChunkTests(unittest.TestCase):
    def test_majority_abstain_and_disagreement(self):
        ep = drop_episode()
        answers = {3: (NE, "none"),                                           # rules say progress (moving approach) -> disagreement
                   7: [(PR, "lift"), (NE, "none"), ("uncertain", "none")],    # no strict majority -> abstain
                   12: (FI, "loss"),                                          # agrees with the rules
                   20: [(NE, "none"), (NE, "none"), (AF, "none")]}            # majority neutral with support 2/3
        answers.update({c: (NE, "none") for c in range(13, 28) if c != 20})   # tail: agree with the rules (9_tail neutral)
        with tempfile.TemporaryDirectory() as tmp:
            backend = OracleBackend(ep, chunk_answers=answers)
            pred = run(oracle_chunk, ep, backend, tmp, drop_reference())
            result = json.loads((Path(tmp) / "oracle_chunk" / "result.json").read_text())
            cached = list((Path(tmp) / "oracle_chunk" / "oracle_chunk").glob("*.json"))
        # one generate_many call with k * n_chunks prompts; no scans, no identification
        self.assertEqual((backend.generate_many_calls, backend.generate_many_prompts, backend.generate_calls), (1, 3 * 28, 0))
        self.assertEqual(pred["n_model_calls"], 1)
        self.assertEqual(len(cached), 28)
        self.assertEqual((pred["chunk_labels"][3], pred["chunk_q"][3]), (NE, 1.0))
        self.assertEqual((pred["chunk_labels"][7], pred["chunk_q"][7]), (None, 0.0))
        self.assertEqual((pred["chunk_labels"][12], pred["chunk_q"][12]), (FI, 1.0))
        self.assertEqual((pred["chunk_labels"][20], pred["chunk_q"][20]), (NE, round(2 / 3, 4)))
        self.assertEqual(pred["chunk_labels"][0], PR)
        # decisive and cause are the rules', events/held object the oracle's
        self.assertEqual((pred["decisive_chunk"], pred["cause"]), (12, "grasp"))
        self.assertEqual(pred["held_object"], "alphabet_soup_1")
        self.assertEqual([e["type"] for e in pred["events"]], ["grasp", "drop"])
        ev = result["evidence"]
        self.assertEqual(ev["rules_decisive_cause"], [12, "grasp"])
        self.assertEqual(ev["rules_chunk_labels"][12], FI)
        self.assertEqual(ev["vlm_vs_rules"]["abstained"], [7])
        self.assertEqual(ev["vlm_vs_rules"]["disagree"], [{"chunk": 3, "vlm": NE, "rules": PR}])
        self.assertEqual((ev["vlm_vs_rules"]["n_answered"], ev["vlm_vs_rules"]["n_agree"]), (27, 26))
        self.assertEqual(ev["vlm_chunks"][12]["votes"], {FI: 3})
        # every chunk prompt carried the true tracker state, the held-object fact and the verified events
        self.assertEqual(len(backend.chunk_texts), 3 * 28)
        self.assertTrue(all("Verified events: grasp of alphabet soup 1 in chunk 5" in t for t in backend.chunk_texts))
        self.assertTrue(all("wrist close-up identification" in t and "alphabet soup 1 (the task target)" in t for t in backend.chunk_texts))
        t12 = next(t for t in backend.chunk_texts if "TARGET chunk 12:" in t)
        self.assertIn("tracker estimate at interval start: held", t12)
        self.assertIn("loss_or_release", t12)
        t2 = next(t for t in backend.chunk_texts if "TARGET chunk 2:" in t)
        self.assertIn("tracker estimate at interval start: not established", t2)  # no tracker transition before chunk 2
        t20 = next(t for t in backend.chunk_texts if "TARGET chunk 20:" in t)
        self.assertIn("tracker estimate at interval start: empty", t20)

    def test_compare_helper_and_cache(self):
        self.assertEqual(oracle_chunk.compare([PR, None, FI], [PR, PR, NE]),
                         {"abstained": [1], "disagree": [{"chunk": 2, "vlm": FI, "rules": NE}], "n_answered": 2, "n_agree": 1, "agreement": 0.5})
        self.assertIsNone(oracle_chunk.compare([None], [PR])["agreement"])
        ep = drop_episode(13)
        with tempfile.TemporaryDirectory() as tmp:
            first = run(oracle_chunk, ep, OracleBackend(ep), tmp, drop_reference(13), via_file=False)
            again = OracleBackend(ep)
            second = run(oracle_chunk, ep, again, tmp, drop_reference(13), via_file=False)
        self.assertEqual((again.generate_many_calls, second["n_model_calls"]), (0, 0))
        self.assertEqual(first["chunk_labels"], second["chunk_labels"])
        self.assertEqual(len(first["chunk_labels"]), 13)
        self.assertTrue(CONTRACT_KEYS.issubset(first))


class OracleMomentTests(unittest.TestCase):
    def test_majority_and_sentences(self):
        ep = drop_episode()
        answers = [moment_json(12, "grasp", "closed the gripper 3 cm left of the can", 0.9),
                   moment_json(11, "grasp", "grasped the can off-centre", 0.7),
                   moment_json(12, "manipulation", "the can slipped while lifting", 0.6),
                   moment_json(12, "grasp", "the grip was too shallow", 0.8),
                   moment_json(30, "grasp", "outside the window", 0.5)]  # chunk outside the window: chunk vote discarded, cause kept
        with tempfile.TemporaryDirectory() as tmp:
            backend = OracleBackend(ep, moment=answers)
            pred = run(oracle_moment, ep, backend, tmp, drop_reference())
            result = json.loads((Path(tmp) / "oracle_moment" / "result.json").read_text())
            cached = list((Path(tmp) / "oracle_moment" / "moment").glob("*.json"))
        self.assertEqual((backend.generate_calls, backend.moment_calls, pred["n_model_calls"], len(cached)), (1, 5, 1, 1))
        self.assertEqual((pred["decisive_chunk"], pred["cause"]), (12, "grasp"))
        # chunk labels are the rules', events/held object the oracle's
        self.assertEqual((pred["chunk_labels"][12], pred["completion_rules"][12]), (FI, "1_drop"))
        self.assertNotIn(None, pred["chunk_labels"])
        self.assertEqual(pred["held_object"], "alphabet_soup_1")
        ev = result["evidence"]
        self.assertEqual(ev["window"], [11, 13])
        self.assertEqual(ev["vlm"]["chunk_votes"], {"11": 1, "12": 3})
        self.assertEqual(ev["vlm"]["cause_votes"], {"grasp": 4, "manipulation": 1})
        self.assertEqual(len(ev["vlm"]["sentences"]), 5)
        self.assertIn("closed the gripper 3 cm left of the can", ev["vlm"]["sentences"])
        self.assertEqual(ev["vlm"]["samples"][4]["in_window"], False)
        self.assertEqual(ev["vlm"]["confidences"][0], 0.9)
        self.assertEqual(ev["rules_decisive_cause"], [12, "grasp"])
        # dense window frames: chunks 11-13 at stride 2 = 15 tiles; the prompt names the window and the facts
        self.assertEqual(ev["n_tiles"], 15)
        text = backend.moment_texts[0]
        self.assertIn("Window under review: chunks 11 to 13 (steps 110-139)", text)
        self.assertIn("Verified events: grasp of alphabet soup 1 in chunk 5", text)
        self.assertIn("alphabet soup = a short DARK BLUE can", text)
        self.assertIn("chunk 12 step 120:", text)
        self.assertTrue(all(110 <= f < 140 for f in ep.frames_seen))

    def test_window_at_episode_edges_and_ties(self):
        self.assertEqual(oracle_moment.window_for(0, 28), (0, 1))
        self.assertEqual(oracle_moment.window_for(27, 28), (26, 27))
        self.assertEqual(oracle_moment.window_for(12, 28), (11, 13))
        samples = [oracle_moment.parse_moment(moment_json(11, "grasp"), 11, 13), oracle_moment.parse_moment(moment_json(13, "manipulation"), 11, 13)]
        decisive, cause, votes = oracle_moment.vote(samples)
        self.assertEqual((decisive, cause), (11, "unclear"))
        self.assertEqual(oracle_moment.vote([]), (None, None, {"chunk_votes": {}, "cause_votes": {}}))
        s = oracle_moment.parse_moment('{"decisive_chunk": "12", "cause": "wrong object", "what_happened": "x", "confidence": "high"}', 11, 13)
        self.assertEqual((s["decisive_chunk"], s["cause"], s["confidence"]), (12, "sequencing_semantic", 0.5))
        with self.assertRaises(Exception):
            oracle_moment.parse_moment("no json", 11, 13)

    def test_null_decisive_falls_back_to_rules_without_vlm(self):
        ep = Ep(28, held_runs=[(60, 279)], cmd=[(57, 1.0)], moving=[(0, 260)])  # held at end, only 2 idle chunks
        with tempfile.TemporaryDirectory() as tmp:
            backend = OracleBackend(ep)
            pred = run(oracle_moment, ep, backend, tmp, held_at_end_reference())
            result = json.loads((Path(tmp) / "oracle_moment" / "result.json").read_text())
            rules = run(oracle_rules, ep, OracleBackend(ep), tmp, held_at_end_reference())
        self.assertEqual((backend.generate_calls, backend.generate_many_calls, pred["n_model_calls"]), (0, 0, 0))
        self.assertIsNone(pred["decisive_chunk"])
        self.assertEqual(pred["cause"], "manipulation")
        self.assertEqual(pred["chunk_labels"], rules["chunk_labels"])
        self.assertEqual([e["type"] for e in pred["events"]], ["grasp"])
        self.assertIsNone(result["evidence"]["window"])
        self.assertIn("no VLM call", result["evidence"]["fallback"])
        self.assertIs(pred["oracle_conditioned"], True)

    def test_all_garbage_abstains_but_keeps_rules_labels(self):
        ep = drop_episode()
        with tempfile.TemporaryDirectory() as tmp:
            pred = run(oracle_moment, ep, OracleBackend(ep, moment=["nope"]), tmp, drop_reference(), via_file=False)
            result = json.loads((Path(tmp) / "oracle_moment" / "result.json").read_text())
        self.assertIsNone(pred["decisive_chunk"])
        self.assertIsNone(pred["cause"])
        self.assertNotIn(None, pred["chunk_labels"])
        self.assertEqual(result["evidence"]["vlm"]["n_parsed"], 0)
        self.assertEqual(len(result["evidence"]["vlm"]["parse_errors"]), 5)

    def test_cache_hit(self):
        ep = drop_episode()
        with tempfile.TemporaryDirectory() as tmp:
            first = run(oracle_moment, ep, OracleBackend(ep), tmp, drop_reference(), via_file=False)
            again = OracleBackend(ep)
            second = run(oracle_moment, ep, again, tmp, drop_reference(), via_file=False)
        self.assertEqual((again.generate_calls, second["n_model_calls"]), (0, 0))
        self.assertEqual((first["decisive_chunk"], first["cause"]), (second["decisive_chunk"], second["cause"]))


class PrivilegeTests(unittest.TestCase):
    def test_no_priv_columns_and_only_episode_frames(self):
        for m in METHODS:
            with self.subTest(method=m.__name__):
                ep = drop_episode()
                ep.accessed = []
                with tempfile.TemporaryDirectory() as tmp:
                    pred = run(m, ep, OracleBackend(ep), tmp, drop_reference(), via_file=False)
                self.assertEqual(ep.accessed, [])  # the oracle enters through the reference file only, never priv.* columns
                self.assertTrue(all(0 <= f < ep.n for f in ep.frames_seen))
                self.assertTrue(CONTRACT_KEYS.issubset(pred))
                self.assertEqual(len(pred["chunk_labels"]), 28)
                self.assertEqual(len(pred["chunk_q"]), 28)


if __name__ == "__main__":
    unittest.main()
