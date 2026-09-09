"""oracle_whole: ORACLE-CONDITIONED whole-episode diagnosis (the production p8 prompt, K=5) with the reference's
events and held object stated as verified facts in the prompt.

Isolates: can the VLM produce the chunk labels, the decisive chunk and the cause from the full episode when it is
told exactly when the object was grasped, dropped or released and what it was? Events and held_object in the
prediction stay the oracle's; only chunk_labels / chunk_q / decisive_chunk / cause come from the VLM (aggregate of
the parsed samples). Reads the reference file: an ablation, never a production annotator.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parents[1]):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _event_first_lib as lib  # noqa: E402
import _oracle_lib as olib  # noqa: E402
import prompt  # noqa: E402
from aggregate import aggregate  # noqa: E402
from render import build_tiles, chunk_signals, signals_table  # noqa: E402
from schema import CAUSES, LABELS, ParseError, parse_annotation  # noqa: E402

TENTATIVE_SUFFIX = " These are tentative visual observations; verify against the episode frames."
VERIFIED_SUFFIX = (" These events and the held object were verified against the simulator state and are correct: do not "
                   "contradict them, use them to place your labels.")

CONFIG = {
    "family": "oracle_conditioned",
    "oracle_conditioned": True,
    "note": olib.NOTE + " oracle_whole is whole_p8's diagnosis prompt with the verified events in the header.",
    "reads_reference_keys": ["events", "held_runs", "target_slot", "n_chunks"],
    "prompt_version": prompt.PROMPT_VERSION,
    "k": 5, "temperature": 0.7, "max_new_tokens": 1200, "batch": 3, "seed": 4300,
    "max_tiles": 40, "tile_scale": 1.5,
    "facts_suffix": VERIFIED_SUFFIX.strip(),
    "mapping": {"chunk_labels": "aggregate chunk_label; anything not in LABELS (incl. uncertain) -> null", "chunk_q": "aggregate chunk_q",
                "decisive_chunk": "aggregate landmarks.decisive_error.value", "cause": "aggregate cause (unclear stays unclear)",
                "events, held_object": "oracle"},
    "expected_calls_per_episode": 1,
}


def build_content(ep, facts_text, cfg=CONFIG):
    outcome = "success" if bool(getattr(ep, "success", False)) else "failure"
    tiles = build_tiles(ep, max_tiles=int(cfg["max_tiles"]), scale=float(cfg["tile_scale"]))
    table = signals_table(chunk_signals(ep))
    glossary = lib.episode_glossary(ep)
    content = prompt.build_user_content(ep.task, outcome, ep.n_chunks, ep.n, ep.fps, tiles, table, glossary, facts_text)
    content[0]["text"] = content[0]["text"].replace(TENTATIVE_SUFFIX, VERIFIED_SUFFIX)
    return content, len(tiles)


def map_aggregate(agg, n_chunks):
    labels = [lab if lab in LABELS else None for lab in list(agg.get("chunk_label") or [])[:n_chunks]]
    labels += [None] * (n_chunks - len(labels))
    q = [float(v) for v in list(agg.get("chunk_q") or [])[:n_chunks]]
    q += [0.0] * (n_chunks - len(q))
    de = ((agg.get("landmarks") or {}).get("decisive_error") or {}).get("value")
    decisive = int(de) if isinstance(de, (int, float)) and not isinstance(de, bool) else None
    cause = agg.get("cause")
    cause = cause if cause in CAUSES else None
    return labels, q, decisive, cause


def run(ep, backend, workdir, cfg=CONFIG, reference=None, ref_dir=None):
    workdir, log, t0, ref, facts, evidence = olib.start(ep, workdir, reference, ref_dir)
    prediction = olib.base_prediction(ep, facts)
    content, n_tiles = build_content(ep, evidence["facts_text"], cfg)
    k = int(cfg["k"])
    row = olib.cached_generate(backend, prompt.SYSTEM, content, workdir, "whole", k=k, temperature=float(cfg["temperature"]),
                               max_new_tokens=int(cfg["max_new_tokens"]), batch=int(cfg["batch"]), seed=int(cfg["seed"]), log=log,
                               settings={"prompt_version": cfg["prompt_version"], "max_tiles": cfg["max_tiles"], "tile_scale": cfg["tile_scale"]})
    parsed, errors = [], []
    for raw in row["raws"]:
        try:
            parsed.append(parse_annotation(raw, ep.n_chunks))
        except (ParseError, ValueError, TypeError) as exc:  # a malformed sample is recorded, not fatal
            errors.append(str(exc)[:200])
    evidence.update({"n_tiles": n_tiles, "n_samples": k, "n_parsed": len(parsed), "parse_errors": errors, "reused_cache": row.get("reused_cache", False)})
    if parsed:
        agg = aggregate(parsed, ep.n_chunks, n_attempted=k)
        labels, q, decisive, cause = map_aggregate(agg, ep.n_chunks)
        prediction.update({"chunk_labels": labels, "chunk_q": q, "decisive_chunk": decisive, "cause": cause})
        evidence["aggregate"] = {key: agg.get(key) for key in ("cause", "cause_votes", "landmarks", "chunk_label", "chunk_q", "failure_symptom",
                                                                "root_cause", "k", "n_invalid", "all_degenerate", "segments")}
    else:
        evidence["aggregate"] = None
    return olib.finish(cfg, prediction, evidence, log, workdir, t0)
