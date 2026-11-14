"""Prepare, collect, review, and export frozen OopsieData teacher traces.

Preparation/verification/review never call an API. Collection is an explicit
command with a dollar ceiling; attempts are append-only and never auto-retried.
"""
import argparse
import base64
from collections import Counter
import json
import math
import os
from pathlib import Path
import shutil
import time

import oopsie_common as common
import annotation_runtime as transport


def sampling(n, fps, hz, cap):
    if n < 1 or fps <= 0 or hz <= 0 or cap < 2:
        raise ValueError("Positive frame count/rates and a cap >= 2 are required")
    stride = max(1, math.ceil(fps / hz), math.ceil((n - 1) / (cap - 1)))
    return sorted(set(range(0, n, stride)) | {n - 1})


def sampling_windows(n, fps, hz, cap, seconds, overlap):
    """Uniform source-time samples with endpoints, without silently lowering Hz."""
    if n < 1 or min(fps, hz, seconds) <= 0 or not 0 <= overlap < seconds or cap < 2:
        raise ValueError("Invalid window sampling settings")
    width, step = max(1, round(seconds * fps)), max(1, round((seconds-overlap) * fps))
    windows = []
    for start in range(0, n, step):
        end = min(n, start+width)
        frames = sorted({start, end-1} | {start+round(k*fps/hz) for k in range(math.ceil((end-start)*hz/fps))
                                         if start+round(k*fps/hz) < end})
        if len(frames) > cap:
            raise ValueError("Window exceeds frame cap; shorten the window instead of thinning evidence")
        windows.append((start, end, frames))
        if end == n:
            break
    return windows


def prepare(config_path, output=None):
    import av
    import h5py
    import numpy as np
    from PIL import Image

    cfg = common.read(config_path)
    root = common.ROOT
    out = Path(output or root / cfg["out"]).resolve()
    if out.exists():
        raise ValueError("Preparation requires a fresh output directory")
    if cfg["format"] != "oopsie_distillation_v1" or cfg["repo"] != common.REPO_ID:
        raise ValueError("Only real OopsieData is supported")
    source = common.inside(root, cfg["source"])
    audit_root = common.inside(root, cfg["audited_inputs"])
    selection = common.read(source / "selection.json")
    audit = common.read(audit_root / "provenance.json")
    camera_path = common.inside(root, cfg["camera_map"])
    camera_map = common.read(camera_path)
    if any(x["repo"] != cfg["repo"] or x["revision"] != cfg["revision"] for x in (selection, audit)):
        raise ValueError("Selection, audit, and configured dataset revision differ")
    if common.sha(camera_path) != audit["camera_map_sha256"]:
        raise ValueError("Camera mapping differs from the audited selection")
    if audit["source_annotations_used_as_model_input"]:
        raise ValueError("Teacher input audit must exclude source annotations")
    dev, test = set(cfg["development_labs"]), set(cfg["test_labs"])
    if dev & test:
        raise ValueError("Development/test labs overlap")
    selected = {e["release_path"]: e for e in selection["episodes"]}
    if len(selected) != len(selection["episodes"]) or len(audit["episodes"]) != len(selected):
        raise ValueError("Duplicate selection or incomplete audited selection")
    out.mkdir(parents=True)
    shutil.copyfile(common.inside(root, cfg["prompt"]), out / "prompt.txt")
    common.write(out / "config.json", cfg)
    shutil.copyfile(camera_path, out / "camera_map.json")
    episodes = []
    for episode in audit["episodes"]:
        eid = episode["id"]
        entry = selected[episode["release_path"]]
        hdf5 = common.inside(source / "source", entry["release_path"])
        if common.sha(hdf5) != entry["release_file_sha256"] or common.sha(hdf5) != episode["hdf5_sha256"]:
            raise ValueError(f"{eid}: HDF5 hash mismatch")
        # Only the native task and schema are read. No episode_annotations access.
        with h5py.File(hdf5, "r") as handle:
            if handle.attrs["schema"] != "oopsiedata_format_v1":
                raise ValueError("Unsupported HDF5 schema")
            task = handle.attrs["language_instruction"]
            if isinstance(task, bytes):
                task = task.decode("utf-8")
            if task != episode["task"]:
                raise ValueError(f"{eid}: task differs from audited native instruction")
        mapping = camera_map["episodes"][eid]
        if not mapping["visually_reviewed"] or not mapping["evidence"]:
            raise ValueError(f"{eid}: unreviewed camera identities")
        cameras = {c["camera"]: c for c in episode["cameras"]}
        chosen = mapping["rubric"]  # All described, nonduplicate views, not positional collages.
        names = [c["camera"] for c in chosen]
        if len(set(names)) != len(names) or not names:
            raise ValueError("Empty or duplicate camera selection")
        if set(names) & mapping["rubric_excluded"].keys() or set(names) | mapping["rubric_excluded"].keys() != cameras.keys():
            raise ValueError("Account for every included/excluded native camera")
        reference = cameras[names[0]]
        n, fps = reference["frames"], reference["fps"]
        if n != int(entry["timestep_count"]):
            raise ValueError("Camera frame count differs from recorded state count")
        windows = (sampling_windows(n, fps, cfg["sample_hz"], cfg["max_frames_per_camera"],
                                    cfg["window_seconds"], cfg["window_overlap_seconds"])
                   if "window_seconds" in cfg else None)
        frames = (sorted({f for _, _, selected_frames in windows for f in selected_frames}) if windows else
                  sampling(n, fps, cfg["sample_hz"], cfg["max_frames_per_camera"]))
        images, seen_hashes, reference_pts = [], set(), None
        for camera in chosen:
            info = cameras[camera["camera"]]
            video = common.inside(source / "source", info["path"])
            if common.sha(video) != info["sha256"] or info["sha256"] in seen_hashes:
                raise ValueError("Changed or duplicate selected camera video")
            seen_hashes.add(info["sha256"])
            pts = []
            with av.open(str(video)) as container:
                for index, frame in enumerate(container.decode(video=0)):
                    if frame.pts is None:
                        raise ValueError("Missing source video PTS")
                    seconds = float(frame.pts * frame.time_base)
                    pts.append(seconds)
                    if index in frames:
                        image = frame.to_image().convert("RGB")
                        image.thumbnail((cfg["max_image_side"], cfg["max_image_side"]), Image.Resampling.LANCZOS)
                        # Camera IDs remain metadata; ordinal filenames avoid interpreting native names as paths.
                        relative = f"images/{eid}/{names.index(camera['camera']):02d}_{index:06d}.jpg"
                        path = out / relative
                        path.parent.mkdir(parents=True, exist_ok=True)
                        image.save(path, quality=95)
                        images.append(dict(frame=index, seconds=seconds, camera=camera["camera"], path=relative))
            if len(pts) != n or not np.allclose(pts, np.arange(n) / fps, rtol=0, atol=1e-4):
                raise ValueError(f"{eid}: inconsistent encoded video clock")
            if reference_pts is not None and not np.allclose(pts, reference_pts, rtol=0, atol=1e-4):
                raise ValueError(f"{eid}: selected camera clocks differ")
            reference_pts = pts
        images.sort(key=lambda x: (x["frame"], names.index(x["camera"])))
        lab = entry["release_path"].split("/")[1]
        split = "test" if lab in test else "development" if lab in dev else "train"
        prepared = dict(id=eid, release_path=entry["release_path"], lab=lab, split=split,
                             task=task, n_frames=n, fps=fps, sampled_frames=frames,
                             cameras=chosen, images=images,
                             camera_exclusions=mapping["rubric_excluded"],
                             original_hdf5_sha256=episode["hdf5_sha256"],
                             original_cameras=[cameras[name] for name in names])
        if cfg.get("annotation_schema"):
            prepared["annotation_schema"] = cfg["annotation_schema"]
        if windows:
            for index, (start, end, selected_frames) in enumerate(windows, 1):
                episodes.append(dict(prepared, id=f"{eid}_W{index:02d}", source_episode_id=eid,
                                     window_start_frame=start, window_end_frame=end,
                                     sampled_frames=selected_frames,
                                     images=[item for item in images if item["frame"] in selected_frames]))
        else:
            episodes.append(prepared)
        print(f"{eid}: {split}, {len(frames)} frames x {len(names)} cameras", flush=True)
    manifest = dict(format=cfg["format"], repo=cfg["repo"], revision=cfg["revision"],
                    input_contract="visual_only_native_cameras_windows_v3" if "window_seconds" in cfg else "visual_only_native_cameras_v1", config=cfg,
                    source_selection_sha256=common.sha(source / "selection.json"),
                    source_audit_sha256=common.sha(audit_root / "provenance.json"),
                    physical_capture_alignment_verified=False,
                    source_annotations_used_as_model_input=False, episodes=episodes,
                    files={p.relative_to(out).as_posix(): common.sha(p) for p in sorted(out.rglob("*")) if p.is_file()})
    common.write(out / "manifest.json", manifest)
    common.verify(out)
    return dict(out=str(out), episodes=len(episodes), images=sum(len(e["images"]) for e in episodes),
                splits=dict(Counter(e["split"] for e in episodes)), api_calls=0)


def payload(root, manifest, episode, teacher):
    cfg = manifest["config"]
    content = []
    for part in common.messages(root, manifest, episode)[0]["content"]:
        if part["type"] == "text":
            content.append(dict(type="input_text", text=part["text"]))
        else:
            encoded = base64.b64encode(common.inside(root, part["image"]).read_bytes()).decode("ascii")
            content.append(dict(type="input_image", detail="high", image_url="data:image/jpeg;base64," + encoded))
    return dict(model=cfg["teachers"][teacher], input=[dict(role="user", content=content)],
                reasoning=dict(effort=cfg["reasoning"]), max_output_tokens=cfg["max_output_tokens"],
                text=dict(format=dict(type="text" if common.annotation_format(manifest) == "markdown" else "json_object")), truncation="disabled", store=False,
                service_tier="default")


def validate(root):
    manifest = common.verify(root)
    result = dict(planned=len(manifest["episodes"]) * len(manifest["config"]["teachers"]),
                  validated=0, invalid=[], pending=[], segment_counts={},
                  generation_estimate_usd=0.0, comparison_reference="teacher proposals, not human ground truth")
    counts = Counter()
    for episode in manifest["episodes"]:
        for teacher in manifest["config"]["teachers"]:
            stem = episode["id"] + "_" + teacher
            folder = Path(root) / "traces" / stem
            if not (folder / "attempt.json").exists():
                result["pending"].append(stem)
                continue
            record = common.read(folder / "attempt.json")
            result["generation_estimate_usd"] += record.get("generation_estimate_usd", 0)
            try:
                if record["status"] != "validated":
                    raise ValueError(record.get("error", record["status"]))
                if record["manifest_sha256"] != common.sha(Path(root) / "manifest.json"):
                    raise ValueError("Trace belongs to a different frozen evidence manifest")
                if record["model"] != manifest["config"]["teachers"][teacher] or record["episode"] != episode["id"]:
                    raise ValueError("Trace teacher or episode differs from the frozen selection")
                value = common.load_annotation(folder, manifest)
                if common.sha(common.annotation_path(folder, manifest)) != record["annotation_sha256"]:
                    raise ValueError("Changed annotation bytes")
                raw = common.read(folder / "response.json")
                if common.sha(folder / "response.json") != record["response_sha256"]:
                    raise ValueError("Changed raw response bytes")
                answer, complete = transport.extract_answer("openai", raw)
                if not complete or common.parse_answer(answer, common.annotation_format(manifest)) != value:
                    raise ValueError("Annotation differs from completed original answer")
                if common.annotation_format(manifest) == "markdown" and common.annotation_path(folder, manifest).read_bytes().decode("utf-8") != answer:
                    raise ValueError("Native Markdown answer changed")
                common.validate_annotation(value, episode)
                result["validated"] += 1
                for segment in value["segments"]:
                    usable = (common.oopsie_markdown.field_masks(segment)["Failure"] if "uncertain_fields" in segment
                              else not segment["review_required"])
                    key = teacher + ":" + ("masked" if not usable else "eligible")
                    counts[key + (":failure" if segment["failure"] else ":nonfailure")] += 1
                    if usable and segment["failure"] and ("uncertain_fields" not in segment or common.oopsie_markdown.field_masks(segment)["Categories"]):
                        counts.update(teacher + ":eligible_category:" + c for c in segment["categories"])
            except (ValueError, KeyError, TypeError, OSError) as exc:
                result["invalid"].append(dict(trace=stem, error=str(exc)))
    result["segment_counts"] = dict(counts)
    return result


def collect(root, budget, limit=None, teachers=None, episodes=None):
    manifest = common.verify(root)
    if budget <= 0 or not math.isfinite(budget):
        raise ValueError("A finite positive collection budget is required")
    if limit is not None and limit < 1:
        raise ValueError("Collection limit must be positive")
    cfg = manifest["config"]
    chosen = teachers or list(cfg["teachers"])
    if not set(chosen) <= cfg["teachers"].keys():
        raise ValueError("Unknown frozen teacher")
    if episodes and not set(episodes) <= {e["id"] for e in manifest["episodes"]}:
        raise ValueError("Unknown frozen episode")
    root = Path(root)
    lock = root / "collection.lock"
    # One collector per run: a second process cannot consume the same budget.
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    try:
        keys = {"openai": transport.credentials()["openai"]}
        reserved = 0.0
        for path in (root / "traces").glob("*/attempt.json"):
            item = common.read(path)
            reserved += item.get("generation_estimate_usd", item.get("reserved_usd", 0))
        sent = 0
        for episode in manifest["episodes"]:
            if episodes and episode["id"] not in episodes:
                continue
            for teacher in chosen:
                folder = root / "traces" / (episode["id"] + "_" + teacher)
                if folder.exists():
                    continue  # Failed/unknown attempts are retained and never resent.
                if limit is not None and sent >= limit:
                    return validate(root)
                body = payload(root, manifest, episode, teacher)
                count_body = {k: body[k] for k in ("model", "input", "reasoning", "text", "truncation")}
                counted = transport.post("https://api.openai.com/v1/responses/input_tokens", "openai", count_body, keys)
                tokens = counted["input_tokens"]
                if type(tokens) is not int or not 0 < tokens <= cfg["max_input_tokens"]:
                    raise ValueError("Frozen teacher input-token ceiling exceeded")
                rates = cfg["rates_per_million"][teacher]
                ceiling = (tokens * max(rates["input"], rates["cache_write"]) + cfg["max_output_tokens"] * rates["output"]) / 1e6
                if reserved + ceiling > budget:
                    raise ValueError(f"Remaining budget cannot reserve next trace (${ceiling:.3f})")
                folder.mkdir(parents=True)
                request_hash = __import__("hashlib").sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
                record = dict(episode=episode["id"], teacher=teacher, model=body["model"],
                              status="in_flight", reserved_usd=ceiling, input_tokens=tokens,
                              request_sha256=request_hash, manifest_sha256=common.sha(root / "manifest.json"),
                              code_sha256={name: common.sha(Path(__file__).parent / name) for name in
                                           ("oopsie_pipeline.py", "oopsie_common.py", "oopsie_markdown.py")},
                              started=time.time())
                transport.atomic_json(folder / "attempt.json", record)
                reserved += ceiling
                try:
                    print(f"{episode['id']}/{teacher}: generating; {tokens} input tokens", flush=True)
                    raw = transport.post("https://api.openai.com/v1/responses", "openai", body, keys)
                    raw = json.loads(transport.redact(json.dumps(raw), keys))
                    common.write(folder / "response.json", raw)
                    record["response_sha256"] = common.sha(folder / "response.json")
                    returned = str(raw.get("model", ""))
                    if returned != body["model"] and not returned.startswith(body["model"] + "-"):
                        raise ValueError("Returned teacher model differs from requested model")
                    usage = raw["usage"]
                    details = usage.get("input_tokens_details") or {}
                    cached, writes = details.get("cached_tokens", 0), details.get("cache_write_tokens", 0)
                    inp, output = usage["input_tokens"], usage["output_tokens"]
                    if any(type(v) is not int or v < 0 for v in (inp, output, cached, writes)) or cached + writes > inp:
                        raise ValueError("Invalid token usage accounting")
                    cost = ((inp - cached - writes) * rates["input"] + cached * rates["cached"] +
                            writes * rates["cache_write"] + output * rates["output"]) / 1e6
                    record.update(usage=usage, generation_estimate_usd=cost, returned_model=returned)
                    answer, complete = transport.extract_answer("openai", raw)
                    (folder / "answer.txt").write_text(answer, encoding="utf-8")
                    if not complete:
                        raise ValueError("Incomplete teacher output; no automatic retry")
                    value = common.parse_answer(answer, common.annotation_format(manifest))
                    common.validate_annotation(value, episode)
                    destination = common.annotation_path(folder, manifest)
                    if common.annotation_format(manifest) == "markdown":
                        destination.write_bytes(answer.encode("utf-8"))
                    else:
                        common.write(destination, value)
                    record.update(status="validated", annotation_sha256=common.sha(destination))
                    reserved += cost - ceiling
                except Exception as exc:
                    record.update(status="stopped", error=transport.redact(str(exc), keys)[:800])
                finally:
                    record["elapsed_seconds"] = time.time() - record["started"]
                    transport.atomic_json(folder / "attempt.json", record)
                sent += 1
                print(f"{episode['id']}/{teacher}: {record['status']}", flush=True)
                if record["status"] != "validated":
                    # Stop on first failure rather than consuming a full batch on a broken setup.
                    return validate(root)
        return validate(root)
    finally:
        lock.unlink()


def review(root):
    from review_oopsie_video import build
    return build(root)


def export(root, out, teacher="sol", decisions=None):
    manifest = common.verify(root)
    summary = validate(root)
    if summary["invalid"]:
        raise ValueError("Resolve stopped/invalid traces before exporting a new dataset")
    choices = common.read(decisions) if decisions else {}
    known = {e["id"] for e in manifest["episodes"]}
    if set(choices) - known:
        raise ValueError("Unknown episode in review decisions")
    out = Path(out)
    if out.exists():
        raise ValueError("Export requires a fresh output directory")
    rows = {s: [] for s in ("train", "development", "test")}
    counts = Counter()
    for episode in manifest["episodes"]:
        decision = choices.get(episode["id"], dict(teacher=teacher))
        selected = decision["teacher"]
        if selected not in manifest["config"]["teachers"]:
            raise ValueError("Decision must select a frozen teacher; adjudications require a separately versioned run")
        folder = Path(root) / "traces" / (episode["id"] + "_" + selected)
        attempt = common.read(folder / "attempt.json")
        if attempt["status"] != "validated":
            raise ValueError("Every exported episode must have a validated selected trace")
        value = common.load_annotation(folder, manifest)
        format = common.annotation_format(manifest)
        original = common.annotation_path(folder, manifest).read_bytes().decode("utf-8")
        target, supervision = common.target_with_masks(value, format, original)
        row = dict(id=episode["id"] + "_" + selected, episode_id=episode["id"], split=episode["split"],
                   target_format=format,
                   messages=common.messages(root, manifest, episode) + [dict(role="assistant", content=target)],
                   supervision=supervision,
                   provenance=dict(repo=manifest["repo"], revision=manifest["revision"],
                                   release_path=episode["release_path"], lab=episode["lab"], teacher=selected,
                                   annotation_sha256=attempt["annotation_sha256"], review_decision=decision,
                                   quality="schema_validated_teacher_proposal"))
        rows[episode["split"]].append(row)
        counts[episode["split"] + ":episodes"] += 1
        counts[episode["split"] + ":eligible_segments"] += sum(s["teacher_loss_mask"] for s in supervision["segments"])
        counts[episode["split"] + ":without_eligible_segments"] += not supervision["has_unflagged_segment_targets"]
    out.mkdir(parents=True)
    for split, records in rows.items():
        with (out / (split + ".jsonl")).open("x", encoding="utf-8") as stream:
            for row in records:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    common.write(out / "export.json", dict(format="oopsie_sft_v1", run=Path(os.path.relpath(root, out)).as_posix(),
                 manifest_sha256=common.sha(Path(root) / "manifest.json"), counts=dict(counts),
                 human_verified=False, reference_scope="Teacher labels only, including development/test. Not human gold.",
                 files={p.name: common.sha(p) for p in out.glob("*.jsonl")}))
    for split in rows:
        common.load_export(out, split)
    return dict(out=str(out), counts=dict(counts))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--config", type=Path, default=common.ROOT / "configs/oopsie_qwen7b_markdown.json")
    p.add_argument("--out", type=Path)
    for name in ("verify", "collect", "validate", "review", "export"):
        p = sub.add_parser(name)
        p.add_argument("--run", type=Path, required=True)
        if name == "collect":
            p.add_argument("--budget-usd", type=float, required=True, help="Run-total ceiling, including previous/unknown attempts")
            p.add_argument("--limit", type=int)
            p.add_argument("--teachers", nargs="+", choices=("sol", "astra"))
            p.add_argument("--episodes", nargs="+")
        if name == "export":
            p.add_argument("--out", type=Path, required=True)
            p.add_argument("--teacher", choices=("sol", "astra"), default="sol")
            p.add_argument("--decisions", type=Path, help="JSON mapping episode IDs to {teacher, reviewer, note}")
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.config, args.out)
    elif args.command == "collect":
        result = collect(args.run, args.budget_usd, args.limit, args.teachers, args.episodes)
    elif args.command == "export":
        result = export(args.run, args.out, args.teacher, args.decisions)
    elif args.command == "verify":
        manifest = common.verify(args.run)
        result = dict(episodes=len(manifest["episodes"]), frozen_inputs_valid=True, api_calls=0)
    else:
        result = globals()[args.command](args.run)
    print(json.dumps(result, indent=2))
    if args.command in ("collect", "validate") and result["invalid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
