"""VLM segmentation of recorded episodes (proposal section 4), local Qwen3-VL backend.

Per episode: route -> render chunk tiles + signal table -> K sampled JSON diagnoses -> parse/validate ->
self-consistency aggregate (per-chunk q) -> optional dense refinement of the landmarks -> one JSON record at
  $FTL_ANNOT/<tag>/<dataset>/episode_XXXXXX.json   (default $FTL_PROJ/annot)
Resumable: existing records are skipped unless --overwrite.

Usage (inside the LeRobot venv, see annotate.sh):
  annotate.py --datasets full_shift8 [full_goal ...] [--episodes 0 3 7] [--k 5] [--limit 20]
              [--failures-only] [--include-clean] [--refine] [--dry-run] [--save-render] [--tag NAME]
  --dry-run      render tiles + prompt only (no model); writes previews to outputs/annot_preview/<dataset>/
  --save-render  also save the contact sheet next to the previews for annotated episodes
"""
import argparse
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aggregate import aggregate, merge_refinement, quality_flags  # noqa: E402
from common import WIN_OUT, Episode, annot_path, dump_json, list_datasets, open_dataset, read_episodes_jsonl  # noqa: E402
from prompt import (IDENTIFY_SYSTEM, PROMPT_VERSION, REFINE_SYSTEM, SYSTEM, build_identify_content, build_refine_content,  # noqa: E402
                    build_user_content, held_object_fact, scene_glossary)
from render import build_tiles, build_window_tiles, build_wrist_tiles, chunk_signals, contact_sheet, holding_chunks, signals_table  # noqa: E402
from route import default_clean_record, route_episode, success_length_medians  # noqa: E402
from schema import LANDMARKS, ParseError, extract_json, parse_annotation  # noqa: E402


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", required=True, help="dataset names or family prefixes (full_shift8 -> full_shift8__t*)")
    ap.add_argument("--episodes", nargs="*", type=int, default=None)
    ap.add_argument("--model", default="Qwen/Qwen3-VL-8B-Instruct")
    ap.add_argument("--tag", default=None, help="annotation set name (default: <model short name>_<prompt version>)")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--batch", type=int, default=3, help="samples decoded per round (halved automatically on OOM); 3 fits 1.5x tiles in 24 GiB")
    ap.add_argument("--tile-scale", type=float, default=1.5, help="upscale factor of the 512x256 chunk tiles shown to the model")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-new-tokens", type=int, default=1200)
    ap.add_argument("--max-tiles", type=int, default=40)
    ap.add_argument("--limit", type=int, default=None, help="max episodes to process in this run (after skipping done ones)")
    ap.add_argument("--failures-only", action="store_true")
    ap.add_argument("--include-clean", action="store_true", help="send clean successes to the VLM too")
    ap.add_argument("--refine", action="store_true", help="dense second pass around every predicted decisive error, including unanimous votes")
    ap.add_argument("--refine-spread", type=int, default=2, help="deprecated; refinement now checks unanimous predictions too")
    ap.add_argument("--no-identify", action="store_true", help="skip the held-object identification call (wrist close-ups at 2x)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--save-render", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args()


def preview_dir(name):
    d = WIN_OUT / "annot_preview" / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_episode(ep, backend, args, medians, tag):
    route = route_episode(ep, medians)
    rec = {
        "schema": "annot_v2", "tag": tag, "model": args.model if route["route"] == "vlm" else None, "prompt_version": PROMPT_VERSION,
        "dataset": ep.name, "episode_index": ep.ep, "suite": ep.meta["suite"], "task_id": ep.meta["task_id"], "task": ep.task,
        "success": ep.success, "recorded_success": bool(ep.meta["success"]), "length": ep.n, "fps": ep.fps, "n_chunks": ep.n_chunks, "chunks": ep.chunks, "route": route,
    }
    if route["route"] == "clean" and not args.include_clean:
        rec["source"] = "oracle_default"
        rec["annotation"] = default_clean_record(ep)
        return rec

    outcome = "success" if ep.success else "failure"
    t0 = time.time()
    tiles = build_tiles(ep, max_tiles=args.max_tiles, scale=args.tile_scale)
    sig = chunk_signals(ep)
    table = signals_table(sig)
    glossary = scene_glossary(list(ep.meta["object_slots"]) + list(ep.meta.get("fixtures", [])) + list(ep.meta["target_objects"]))
    render_s = time.time() - t0

    # Independent, time-specific observations; never promote identification to ground truth.
    facts = ""
    hold = holding_chunks(sig)
    if hold and not args.no_identify and not args.dry_run:
        import json as _json
        observations = []
        rec["identify"] = []
        for c in hold:
            wt = build_wrist_tiles(ep, [c], scale=2.0)
            raw = backend.generate(IDENTIFY_SYSTEM, build_identify_content(ep.task, glossary, wt),
                                   k=1, temperature=0.0, max_new_tokens=200, batch=1)[0]
            ident = {"chunk": c, "raw": raw, "gen": dict(backend.last)}
            try:
                d = _json.loads(extract_json(raw))
                ident["parsed"] = d
                ans = str(d.get("held_object") or "").lower().strip().replace(" ", "_")
                candidates = [name for name in ep.meta["object_slots"]
                              if ans in (name, name.rsplit("_", 1)[0])]
                if len(candidates) == 1:
                    ident["held"] = candidates[0]
                    observations.append(f"At the midpoint observation of chunk {c}, a separate visual pass suggests "
                                        f"{candidates[0]} may be held. This does not describe other frames or chunks.")
            except Exception as e:
                ident["error"] = str(e)
            rec["identify"].append(ident)
        facts = "\n".join(observations)
    content = build_user_content(ep.task, outcome, ep.n_chunks, ep.n, ep.fps, tiles, table, glossary, facts)
    rec["render"] = {"n_tiles": len(tiles), "tile_scale": args.tile_scale, "tile_chunks": [t[2] for t in tiles], "render_s": round(render_s, 1), "signals": sig}

    if args.dry_run or args.save_render:
        pd = preview_dir(ep.name)
        contact_sheet(tiles).save(pd / f"ep{ep.ep:04d}_{'ok' if ep.success else 'FAIL'}_sheet.png")
        (pd / f"ep{ep.ep:04d}_prompt.txt").write_text(SYSTEM + "\n\n=== USER ===\n" + "\n".join(
            b["text"] if b["type"] == "text" else "[image]" for b in content), encoding="utf-8")
    if args.dry_run:
        rec["source"] = "dry_run"
        return rec

    raws = backend.generate(SYSTEM, content, k=args.k, temperature=args.temperature, max_new_tokens=args.max_new_tokens, batch=args.batch)
    gen_info = dict(backend.last)
    parsed, samples = [], []
    for i, raw in enumerate(raws):
        try:
            a = parse_annotation(raw, ep.n_chunks)
            if a.outcome != outcome:
                raise ParseError("outcome disagrees with corrected episode outcome")
            parsed.append(a)
            samples.append({"i": i, "ok": True, "raw": raw, "parsed": a.model_dump()})
        except ParseError as e:
            samples.append({"i": i, "ok": False, "error": str(e), "raw": raw})
    # one re-sample round for the failed ones
    n_bad = sum(not s["ok"] for s in samples)
    if n_bad:
        extra = backend.generate(SYSTEM, content, k=n_bad, temperature=args.temperature, max_new_tokens=args.max_new_tokens, batch=args.batch)
        for raw in extra:
            try:
                a = parse_annotation(raw, ep.n_chunks)
                if a.outcome != outcome:
                    raise ParseError("outcome disagrees with corrected episode outcome")
                parsed.append(a)
                samples.append({"i": len(samples), "ok": True, "retry": True, "raw": raw, "parsed": a.model_dump()})
            except ParseError as e:
                samples.append({"i": len(samples), "ok": False, "retry": True, "error": str(e), "raw": raw})
    if not parsed:
        rec["source"] = "vlm_failed"
        rec["samples"] = samples
        rec["gen"] = gen_info
        return rec

    agg = aggregate(parsed, ep.n_chunks, n_attempted=len(samples))
    rec["source"] = "vlm"
    rec["samples"] = samples
    rec["gen"] = gen_info

    if args.refine and not ep.success:
        de = agg["landmarks"]["decisive_error"]
        if de["value"] is not None:
            lo = max(0, de["value"] - 3)
            hi = min(ep.n_chunks - 1, de["value"] + 3)
            wt = build_window_tiles(ep, lo, hi, stride=2, scale=args.tile_scale)
            wtable = signals_table([r for r in sig if lo <= r["chunk"] <= hi])
            coarse = {"cause": agg["cause"], "failure_symptom": agg["failure_symptom"], **{k: agg["landmarks"][k]["value"] for k in LANDMARKS}}
            rraws = backend.generate(REFINE_SYSTEM, build_refine_content(ep.task, coarse, wt, wtable), k=args.k,
                                     temperature=args.temperature, max_new_tokens=300, batch=args.batch)
            refined = []
            for raw in rraws:
                try:
                    import json as _json

                    d = _json.loads(extract_json(raw))
                    for key in LANDMARKS:
                        value = d.get(key)
                        if value is not None and (type(value) is not int or not lo <= value <= hi):
                            raise ValueError(f"invalid refined {key}: {value}")
                    refined.append({k: d.get(k) for k in LANDMARKS})
                except Exception as e:  # noqa: BLE001
                    refined.append({"error": str(e)})
            rec["refine"] = {"window": [lo, hi], "n_tiles": len(wt), "samples": refined, "gen": dict(backend.last)}
            agg = merge_refinement(agg, refined, window=(lo, hi))
    agg["quality_flags"] = quality_flags(agg)
    agg["needs_review"] = bool(agg["quality_flags"])
    rec["annotation"] = agg
    return rec


def main():
    args = parse_args()
    tag = args.tag or f"{args.model.split('/')[-1].lower().replace('-instruct', '')}_{PROMPT_VERSION}"
    names = list_datasets(args.datasets)
    if not names:
        sys.exit(f"no datasets match {args.datasets}")
    medians = success_length_medians(names)
    print(f"tag={tag} datasets={len(names)} k={args.k} dry_run={args.dry_run}", flush=True)

    backend = None
    if not args.dry_run:
        from backend_qwen import QwenBackend

        backend = QwenBackend(args.model)
        print(f"loaded {args.model} in {backend.load_s:.0f}s", flush=True)

    done = 0
    stats = {"vlm": 0, "clean": 0, "skipped": 0, "failed": 0}
    for name in names:
        eps = read_episodes_jsonl(name)
        wanted = [e["episode_index"] for e in eps if (args.episodes is None or e["episode_index"] in args.episodes) and not (args.failures_only and e["success"])]
        if not args.overwrite:
            for e in wanted:
                path = annot_path(tag, name, e)
                if path.exists():
                    existing = json.loads(path.read_text())
                    if existing.get("prompt_version") != PROMPT_VERSION or existing.get("schema") != "annot_v2":
                        raise ValueError(f"{path}: incompatible existing record; use a new tag or --overwrite")
        todo = [e for e in wanted if args.overwrite or not annot_path(tag, name, e).exists()]
        stats["skipped"] += len(wanted) - len(todo)
        if not todo:
            continue
        ds = open_dataset(name)
        for e in todo:
            if args.limit is not None and done >= args.limit:
                break
            t0 = time.time()
            ep = Episode(ds, name, e)
            try:
                rec = run_episode(ep, backend, args, medians, tag)
            except Exception:  # noqa: BLE001
                traceback.print_exc()
                stats["failed"] += 1
                continue
            rec["wall_s"] = round(time.time() - t0, 1)
            if not args.dry_run:
                dump_json(rec, annot_path(tag, name, e))
            done += 1
            src = rec["source"]
            stats["vlm" if src == "vlm" else "clean" if src == "oracle_default" else "failed" if src == "vlm_failed" else "vlm"] += 1
            a = rec.get("annotation") or {}
            lm = a.get("landmarks", {}).get("decisive_error", {})
            print(f"{name} ep{e:04d} ok={int(ep.success)} n={ep.n_chunks}ch route={'/'.join(rec['route']['reasons'])} src={src} "
                  f"cause={a.get('cause')} t*={lm.get('value')}(spread {lm.get('spread')}) mean_q={a.get('mean_q')} "
                  f"gen={rec.get('gen', {}).get('gen_s', '-')}s in_tok={rec.get('gen', {}).get('input_tokens', '-')} "
                  f"mem={rec.get('gen', {}).get('max_mem_gb', '-')}GB wall={rec['wall_s']}s", flush=True)
        if args.limit is not None and done >= args.limit:
            break
    print(f"done={done} {stats}", flush=True)


if __name__ == "__main__":
    main()
