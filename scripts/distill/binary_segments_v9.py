"""Whole-episode binary V9 teacher experiments. No SFT or legacy-label rewriting."""
import argparse
import base64
from datetime import datetime, timezone
from itertools import combinations
import json
import math
import os
from pathlib import Path
import re
import shutil
import time
import uuid

import oopsie_common as common
import annotation_runtime as transport

PROTOCOL = "binary_failure_v9"


def parse(text, episode):
    """Strict Markdown-only partition, with no hidden action/category schema."""
    if not isinstance(text, str):
        raise ValueError("Return a Markdown string")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 4 or lines[0] != "# Episode: " + episode["id"]:
        raise ValueError("Expected the episode heading and binary segment table")
    if lines[1] != "| Start frame | End frame | Failure |" or not re.fullmatch(r"\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|", lines[2]):
        raise ValueError("Expected exactly Start frame, End frame, and Failure columns")
    segments, cursor = [], 0
    for line in lines[3:]:
        match = re.fullmatch(r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(Yes|No)\s*\|", line)
        if not match:
            raise ValueError("Each row must contain only integer boundaries and Yes/No")
        start, end, failure = int(match[1]), int(match[2]), match[3] == "Yes"
        if start != cursor or not start < end <= episode["n_frames"]:
            raise ValueError("Segments must cover the episode without gaps, overlaps or invalid boundaries")
        if segments and segments[-1]["failure"] == failure:
            raise ValueError("Merge adjacent segments with the same label")
        segments.append(dict(start_frame=start, end_frame=end, failure=failure))
        cursor = end
    if cursor != episode["n_frames"]:
        raise ValueError("The final segment must end at the source frame count")
    return segments


def pack_camera_views(root, episode):
    """Pack synchronized views without removing frames or shrinking their pixels."""
    from PIL import Image
    source_images = episode['images']
    packed = []
    count = len(episode['cameras'])
    for frame in range(episode['n_frames']):
        sources = source_images[frame*count:(frame+1)*count]
        images = []
        for source in sources:
            with Image.open(common.inside(root, source['path'])) as image:
                images.append(image.convert('RGB'))
        canvas = Image.new('RGB', (sum(i.width for i in images), max(i.height for i in images)), 'black')
        x, panels = 0, []
        for source, image in zip(sources, images, strict=True):
            canvas.paste(image, (x, 0))
            panels.append(dict(camera=source['camera'], x=x, y=0, width=image.width,
                               height=image.height, source_path=source['path']))
            x += image.width
        relative = f"strips/{episode['id']}/{frame:06d}.png"
        path = common.inside(root, relative); path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(path)  # Lossless packing of the already-frozen 280 px JPEG views.
        packed.append(dict(frame=frame, seconds=sources[0]['seconds'], camera='all camera panels',
                           path=relative, panels=panels))
    episode['source_images'], episode['images'] = source_images, packed


def request_rates(cfg, teacher, input_tokens):
    rates = dict(cfg['rates_per_million'][teacher])
    long = cfg.get('long_context_pricing')
    if long and input_tokens > long['threshold_input_tokens']:
        for name in ('input', 'cached', 'cache_write'):
            rates[name] *= long['input_multiplier']
        rates['output'] *= long['output_multiplier']
    return rates


def prepare(config_path):
    import av
    from PIL import Image
    cfg = common.read(config_path)
    if cfg["protocol"] != PROTOCOL or cfg["evidence"] != "all_recorded_frames_full_episode":
        raise ValueError("V9 requires the binary protocol and full recorded-frame evidence")
    if type(cfg["repeats"]) is not int or cfg["repeats"] < 1:
        raise ValueError("Positive repeat count required")
    out = common.inside(common.ROOT, cfg["out"])
    if out.exists():
        raise ValueError("Prepare a fresh versioned run; existing runs are preserved")
    source_run = common.inside(common.ROOT, cfg["source_run"])
    original = common.verify(source_run)
    if len(set(cfg["episodes"])) != len(cfg["episodes"]) or not set(cfg["episodes"]) <= {e["id"] for e in original["episodes"]}:
        raise ValueError("Unknown or duplicate original episode IDs")
    source = common.inside(common.ROOT, original["config"]["source"]) / "source"
    out.mkdir(parents=True)
    common.write(out / "config.json", cfg)
    shutil.copyfile(common.inside(common.ROOT, cfg["prompt"]), out / "prompt.md")
    episodes = []
    for episode in original["episodes"]:
        if episode["id"] not in cfg["episodes"]:
            continue
        item = {k: episode[k] for k in ("id", "release_path", "task", "lab", "split", "fps", "n_frames", "cameras", "original_cameras")}
        item["images"], item["videos"] = [], []
        for index, camera in enumerate(episode["cameras"]):
            info = next(c for c in episode["original_cameras"] if c["camera"] == camera["camera"])
            video = common.inside(source, info["path"])
            if common.sha(video) != info["sha256"]:
                raise ValueError("Original camera recording changed")
            relative_video = f"videos/{episode['id']}/{index:02d}.mp4"
            dest = out / relative_video
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(video, dest)
            except OSError:
                shutil.copyfile(video, dest)
            item["videos"].append(dict(camera=camera["camera"], description=camera["description"], url=relative_video))
            count = 0
            with av.open(str(video)) as container:
                for frame_index, frame in enumerate(container.decode(video=0)):
                    seconds = float(frame.pts * frame.time_base) if frame.pts is not None else None
                    if seconds is None or not math.isclose(seconds, frame_index / episode["fps"], abs_tol=1e-4):
                        raise ValueError("Camera frame timestamps differ from the audited source grid")
                    image = frame.to_image().convert("RGB")
                    image.thumbnail((cfg["max_image_side"], cfg["max_image_side"]), Image.Resampling.LANCZOS)
                    relative = f"images/{episode['id']}/{index:02d}_{frame_index:06d}.jpg"
                    path = out / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    image.save(path, quality=95)
                    item["images"].append(dict(frame=frame_index, seconds=seconds, camera=camera["camera"], path=relative))
                    count += 1
            if count != episode["n_frames"]:
                raise ValueError("Decoded frame count differs from the audited source")
        order = {c["camera"]: i for i, c in enumerate(episode["cameras"])}
        item["images"].sort(key=lambda x: (x["frame"], order[x["camera"]]))
        layout = cfg.get('camera_layout', 'separate_images')
        if layout == 'synchronized_camera_strip':
            pack_camera_views(out, item)
        elif layout != 'separate_images':
            raise ValueError('Unknown camera layout')
        if len(item['images']) > 1500:
            raise ValueError('Whole-episode request exceeds the documented 1500-image API limit')
        episodes.append(item)
    common.write(out / "manifest.json", dict(protocol=PROTOCOL, repo=original["repo"], revision=original["revision"],
        config=cfg, source_manifest_sha256=common.sha(source_run / "manifest.json"),
        source_annotations_used_as_model_input=False, episodes=episodes,
        files={p.relative_to(out).as_posix(): common.sha(p) for p in sorted(out.rglob("*")) if p.is_file()}))
    verify(out)
    return dict(out=str(out), episodes=len(episodes), images=sum(len(e["images"]) for e in episodes), api_calls=0)


def verify(root):
    root = Path(root)
    m = common.read(root / "manifest.json")
    if m["protocol"] != PROTOCOL or m["repo"] != common.REPO_ID or m["source_annotations_used_as_model_input"]:
        raise ValueError("Expected frozen visual-only real OopsieData V9 inputs")
    if m["config"]["evidence"] != "all_recorded_frames_full_episode":
        raise ValueError("Every source frame must be supplied")
    for name, digest in m["files"].items():
        if common.sha(common.inside(root, name)) != digest:
            raise ValueError("Changed frozen input: " + name)
    if {e["id"] for e in m["episodes"]} != set(m["config"]["episodes"]):
        raise ValueError("Episode selection changed")
    seen, labs = set(), {}
    for e in m["episodes"]:
        if e["release_path"] in seen or labs.get(e["lab"], e["split"]) != e["split"]:
            raise ValueError("Duplicate source identity or split leakage")
        seen.add(e["release_path"]); labs[e["lab"]] = e["split"]
        layout = m['config'].get('camera_layout', 'separate_images')
        original_images = e['source_images'] if layout == 'synchronized_camera_strip' else e['images']
        pairs = [(x["frame"], x["camera"]) for x in original_images]
        expected = [(f, c["camera"]) for f in range(e["n_frames"]) for c in e["cameras"]]
        if pairs != expected or any(x["path"] not in m["files"] for x in original_images + e['images']):
            raise ValueError("Missing, reordered or duplicate full-rate camera frames")
        if layout == 'synchronized_camera_strip':
            if [x['frame'] for x in e['images']] != list(range(e['n_frames'])):
                raise ValueError('Missing or reordered synchronized frame strip')
            count = len(e['cameras'])
            for image in e['images']:
                sources = original_images[image['frame']*count:(image['frame']+1)*count]
                if [(p['camera'],p['source_path']) for p in image['panels']] != [(s['camera'],s['path']) for s in sources]:
                    raise ValueError('Camera strip does not account for every original view')
    return m


def payload(root, m, e, teacher):
    root = Path(root)
    info = (f"\n\n## Episode input\n\n- Episode: {e['id']}\n- Task: {e['task']}\n"
            f"- Source frame count: {e['n_frames']}\n- Frames per second: {e['fps']}\n"
            "- Every recorded frame from every listed camera is supplied, in time order.\n\n### Cameras\n\n" +
            "\n".join(f"- {c['camera']}: {c['description']}" for c in e["cameras"]))
    content = [dict(type="input_text", text=(root/"prompt.md").read_text(encoding="utf-8") + info)]
    if m['config'].get('camera_layout') == 'synchronized_camera_strip':
        content[0]['text'] += ('\n\nEach supplied image is one original source frame with synchronized camera panels '
            'placed side by side. Read panels from left to right in the listed Cameras order. '
            'Each panel retains its per-camera resolution; black padding is not scene content. '
            'All recorded timestamps and all listed views are included; no temporal sampling is applied.')
    for x in e["images"]:
        content.append(dict(type="input_text", text=f"Frame {x['frame']} | {x['seconds']:.6f} seconds | camera {x['camera']}"))
        encoded = base64.b64encode(common.inside(root, x["path"]).read_bytes()).decode("ascii")
        mime = 'image/png' if x['path'].endswith('.png') else 'image/jpeg'
        content.append(dict(type="input_image", image_url=f"data:{mime};base64,"+encoded, detail="high"))
    return dict(model=m["config"]["teachers"][teacher], input=[dict(role="user", content=content)],
                reasoning=dict(effort=m["config"]["reasoning"]), max_output_tokens=m["config"]["max_output_tokens"],
                text=dict(format=dict(type="text")), truncation="disabled", store=False, service_tier="default")


def trace_name(eid, teacher, repeat):
    return f"{eid}_{teacher}_r{repeat:02d}"


def load_trace(root, m, e, teacher, repeat):
    folder = Path(root)/"traces"/trace_name(e["id"], teacher, repeat)
    state = common.read(folder/"attempt.json")
    if state["status"] != "validated" or state["manifest_sha256"] != common.sha(Path(root)/"manifest.json"):
        raise ValueError("Trace is unfinished, invalid, or belongs to another input manifest")
    if state["episode"] != e["id"] or state["teacher"] != teacher or state["repeat"] != repeat:
        raise ValueError("Trace identity changed")
    if state["model"] != m["config"]["teachers"][teacher]:
        raise ValueError("Trace teacher differs from the frozen configuration")
    request_file = Path(root)/"requests"/f"{e['id']}_{teacher}.json"
    if common.sha(request_file) != state["request_sha256"]:
        raise ValueError("Frozen transport request changed")
    for name, key in [("response.json", "response_sha256"), ("annotation.md", "annotation_sha256")]:
        if common.sha(folder/name) != state[key]:
            raise ValueError("Changed original teacher output")
    answer, completed = transport.extract_answer("openai", common.read(folder/"response.json"))
    text = (folder/"annotation.md").read_bytes().decode("utf-8")
    if not completed or answer != text:
        raise ValueError("Native Markdown differs from completed original answer")
    return parse(text, e), state


def validate(root):
    m = verify(root)
    result = dict(planned=len(m["episodes"])*len(m["config"]["teachers"])*m["config"]["repeats"],
                  validated=0, pending=[], invalid=[], generation_estimate_usd=0, traces=[])
    for e in m["episodes"]:
        for teacher in m["config"]["teachers"]:
            for repeat in range(1, m["config"]["repeats"]+1):
                name = trace_name(e["id"], teacher, repeat)
                path = Path(root)/"traces"/name/"attempt.json"
                if not path.exists():
                    result["pending"].append(name); continue
                state = common.read(path)
                result["generation_estimate_usd"] += state.get("generation_estimate_usd", 0)
                if state["status"] == "in_flight":
                    result["pending"].append(name); continue
                if state['status'] == 'stopped':
                    result['invalid'].append(dict(trace=name,error=state.get('error','Stopped request; no accepted annotation'),status='stopped'))
                    continue
                try:
                    segments, _ = load_trace(root, m, e, teacher, repeat)
                    result["validated"] += 1
                    result["traces"].append(dict(episode=e["id"], teacher=teacher, repeat=repeat, segments=segments))
                except (ValueError, KeyError, OSError, TypeError) as exc:
                    result["invalid"].append(dict(trace=name, error=str(exc)))
    return result


def preflight(root):
    """Count every frozen request and its cost ceiling before any generation."""
    root = Path(root); m = verify(root)
    keys = {'openai': transport.credentials()['openai']}
    requests = root/'requests'; requests.mkdir(exist_ok=True)
    records = []
    for episode in m['episodes']:
        for teacher in m['config']['teachers']:
            body = payload(root,m,episode,teacher)
            size = len(json.dumps(body).encode('utf-8'))
            if len(episode['images']) > 1500 or size > 512*1024*1024:
                raise ValueError('Request exceeds documented image-count or payload-size limit')
            request_file = requests/f"{episode['id']}_{teacher}.json"
            if not request_file.exists():
                common.write(request_file,body)
            elif common.read(request_file) != body:
                raise ValueError('Frozen request changed')
            count = transport.post('https://api.openai.com/v1/responses/input_tokens','openai',
                {k:body[k] for k in ('model','input','reasoning','text','truncation')},keys)['input_tokens']
            if type(count) is not int or not 0 < count <= m['config']['max_input_tokens']:
                raise ValueError('Frozen input-token ceiling exceeded; no truncation')
            rates = request_rates(m['config'],teacher,count)
            ceiling = (count*max(rates['input'],rates['cache_write'])+m['config']['max_output_tokens']*rates['output'])/1e6
            records.append(dict(episode=episode['id'],teacher=teacher,input_tokens=count,
                request_sha256=common.sha(request_file),image_count=len(episode['images']),
                request_bytes=size,per_call_ceiling_usd=ceiling))
            transport.atomic_json(root/'token_preflight.json',dict(
                manifest_sha256=common.sha(root/'manifest.json'),complete=False,requests=records))
            print(f"{episode['id']} {teacher}: {count} tokens; {len(episode['images'])} images",flush=True)
    result = dict(manifest_sha256=common.sha(root/'manifest.json'),complete=True,requests=records,
                  run_total_ceiling_usd=sum(x['per_call_ceiling_usd'] for x in records)*m['config']['repeats'],
                  generation_calls=0)
    transport.atomic_json(root/'token_preflight.json',result)
    return result


def collect(root, budget):
    root = Path(root); m = verify(root)
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("Finite positive run-total budget required")
    lock = root/"collection.lock"
    with lock.open("x") as stream:
        stream.write(str(os.getpid()))
    try:
        keys = {"openai": transport.credentials()["openai"]}
        reserved = sum((x.get("generation_estimate_usd", x.get("reserved_usd", 0)))
                       for x in (common.read(p) for p in (root/"traces").glob("*/attempt.json")))
        # Run all models once before repeat two, keeping each repeat independent.
        for repeat in range(1, m["config"]["repeats"]+1):
            for e in m["episodes"]:
                for teacher in m["config"]["teachers"]:
                    folder = root/"traces"/trace_name(e["id"], teacher, repeat)
                    if folder.exists():
                        state = common.read(folder/"attempt.json")
                        if state["status"] != "validated":
                            raise ValueError("Inspect the existing unfinished/stopped trace; it will not be resent")
                        continue
                    body = payload(root, m, e, teacher)
                    receipt_path = root/'token_preflight.json'
                    receipt = common.read(receipt_path) if receipt_path.exists() else None
                    if receipt:
                        request_file = root/'requests'/f"{e['id']}_{teacher}.json"
                        if not receipt['complete'] or receipt['manifest_sha256'] != common.sha(root/'manifest.json'):
                            raise ValueError('Preflight must be complete and match frozen inputs')
                        previous = next(r for r in receipt['requests'] if (r['episode'],r['teacher'])==(e['id'],teacher))
                        if previous['request_sha256'] != common.sha(request_file) or common.read(request_file) != body:
                            raise ValueError('Preflight request changed')
                        count = previous['input_tokens']
                    else:
                        count = transport.post("https://api.openai.com/v1/responses/input_tokens", "openai",
                            {k: body[k] for k in ("model", "input", "reasoning", "text", "truncation")}, keys)["input_tokens"]
                    if type(count) is not int or not 0 < count <= m["config"]["max_input_tokens"]:
                        raise ValueError("Frozen input-token ceiling exceeded; no truncation")
                    rates = request_rates(m['config'], teacher, count)
                    ceiling = (count*max(rates["input"], rates["cache_write"]) + m["config"]["max_output_tokens"]*rates["output"])/1e6
                    if reserved+ceiling > budget:
                        raise ValueError("Cannot reserve next independent call within run-total budget")
                    folder.mkdir(parents=True)
                    # Freeze the actual transport request once per teacher/episode.
                    requests = root/"requests"; requests.mkdir(exist_ok=True)
                    request_file = requests/f"{e['id']}_{teacher}.json"
                    if not request_file.exists():
                        common.write(request_file, body)
                    elif common.read(request_file) != body:
                        raise ValueError("Repeated call differs from the original frozen request")
                    state = dict(episode=e["id"], teacher=teacher, repeat=repeat, model=body["model"], status="in_flight",
                        input_tokens=count, reserved_usd=ceiling, manifest_sha256=common.sha(root/"manifest.json"),
                        request_sha256=common.sha(request_file), code_sha256=common.sha(Path(__file__)), started_utc=datetime.now(timezone.utc).isoformat())
                    transport.atomic_json(folder/"attempt.json", state); reserved += ceiling
                    print(f"{folder.name}: generating; {count} input tokens", flush=True)
                    try:
                        raw = transport.post("https://api.openai.com/v1/responses", "openai", body, keys)
                        raw = json.loads(transport.redact(json.dumps(raw), keys))
                        common.write(folder/"response.json", raw)
                        state["response_sha256"] = common.sha(folder/"response.json")
                        returned = str(raw.get("model", ""))
                        if returned != body["model"] and not returned.startswith(body["model"]+"-"):
                            raise ValueError("Returned teacher differs from requested model")
                        u = raw["usage"]; d = u.get("input_tokens_details") or {}
                        inp, out, cached, writes = u["input_tokens"], u["output_tokens"], d.get("cached_tokens", 0), d.get("cache_write_tokens", 0)
                        if any(type(v) is not int or v < 0 for v in (inp,out,cached,writes)) or cached+writes > inp:
                            raise ValueError("Invalid token usage accounting")
                        cost = ((inp-cached-writes)*rates["input"]+cached*rates["cached"]+writes*rates["cache_write"]+out*rates["output"])/1e6
                        state.update(usage=u, returned_model=returned, generation_estimate_usd=cost)
                        answer, completed = transport.extract_answer("openai", raw)
                        (folder/"answer.txt").write_bytes(answer.encode("utf-8"))
                        if not completed:
                            raise ValueError("Incomplete response; no automatic retry")
                        parse(answer, e)
                        (folder/"annotation.md").write_bytes(answer.encode("utf-8"))
                        state.update(status="validated", annotation_sha256=common.sha(folder/"annotation.md"))
                        reserved += cost-ceiling
                    except Exception as exc:
                        state.update(status="stopped", error=transport.redact(str(exc), keys)[:1000])
                    finally:
                        transport.atomic_json(folder/"attempt.json", state)
                    print(folder.name+": "+state["status"], flush=True)
                    if state["status"] != "validated":
                        return validate(root)
        return validate(root)
    finally:
        lock.unlink()


def compare(a, b, n):
    left = {f for s in a if s["failure"] for f in range(s["start_frame"],s["end_frame"])}
    right = {f for s in b if s["failure"] for f in range(s["start_frame"],s["end_frame"])}
    return dict(frame_agreement=1-len(left^right)/n, failure_iou=len(left&right)/len(left|right) if left|right else None,
                both_no_failure=not(left|right), positive_frames_left=len(left), positive_frames_right=len(right),
                frames=n, disagreement_frames=len(left^right), joint_failure_frames=len(left&right),
                failure_union_frames=len(left|right))


def report(root):
    root = Path(root); m = verify(root); result = validate(root)
    pairs = []
    for e in m["episodes"]:
        traces = [r for r in result["traces"] if r["episode"] == e["id"]]
        for a, b in combinations(traces, 2):
            pairs.append(dict(episode=e["id"], left=f"{a['teacher']} r{a['repeat']}", right=f"{b['teacher']} r{b['repeat']}",
                kind="within_teacher" if a["teacher"]==b["teacher"] else "between_teachers", **compare(a["segments"],b["segments"],e["n_frames"])))
    between = [p for p in pairs if p['kind']=='between_teachers']
    denominator = sum(p['frames'] for p in between)
    union = sum(p['failure_union_frames'] for p in between)
    aggregate = dict(
        between_teacher_micro_frame_agreement=(1-sum(p['disagreement_frames'] for p in between)/denominator) if denominator else None,
        between_teacher_macro_frame_agreement=sum(p['frame_agreement'] for p in between)/len(between) if between else None,
        between_teacher_failure_iou=sum(p['joint_failure_frames'] for p in between)/union if union else None,
        positive_episode_ids=sorted({r['episode'] for r in result['traces'] if any(s['failure'] for s in r['segments'])}),
        human_reference_accuracy=None)
    transport.atomic_json(root/"results.json", dict(result, comparisons=pairs, aggregate=aggregate))
    lines=["# Binary failure segmentation " + m["config"].get("prompt_revision", "v9").upper(), "", f"- Validated: {result['validated']} / {result['planned']} independent teacher calls.",
        "- Input: complete episodes, every recorded frame from every selected native camera; images retain the existing 280 px maximum side.",
        "- Output: native Markdown with only start frame, end frame, and binary failure label.",
        "- Three repeats per teacher measure repeatability, not correctness. Agreement is not human-verified accuracy.",
        f"- Estimated generation cost at frozen rates: ${result['generation_estimate_usd']:.6f}.",
        "- No distillation or training export has been performed.", "", "## Teacher segments", "",
        "| Episode | Teacher | Repeat | Failure intervals (seconds) |", "| --- | --- | ---: | --- |"]
    episodes={e["id"]:e for e in m["episodes"]}
    for row in result["traces"]:
        fps=episodes[row["episode"]]["fps"]
        intervals=", ".join(f"{s['start_frame']/fps:.2f}–{s['end_frame']/fps:.2f}" for s in row["segments"] if s["failure"]) or "None proposed"
        lines.append(f"| {row['episode']} | {row['teacher'].title()} | {row['repeat']} | {intervals} |")
    lines += ['', '## Aggregate teacher agreement', '']
    if denominator:
        lines += [f"- Frame-weighted Sol/Astra agreement: {100*aggregate['between_teacher_micro_frame_agreement']:.2f}%.",
                  f"- Mean episode/pair Sol/Astra agreement: {100*aggregate['between_teacher_macro_frame_agreement']:.2f}%.",
                  '- Failure IoU over pooled positive unions: '+(f"{aggregate['between_teacher_failure_iou']:.3f}." if union else 'undefined (no positive union).'),
                  f"- Episodes with any proposed failure: {', '.join(aggregate['positive_episode_ids']) or 'none'}.",
                  '- Pairwise repeats reuse the same recordings; these are not independent evaluation episodes.',
                  '- Human-reference accuracy is not measured. High non-failure prevalence can inflate agreement.']
    lines += ["", "## Repeatability and teacher agreement", "", "| Episode | Pair | Frame agreement | Failure IoU |", "| --- | --- | ---: | ---: |"]
    for p in pairs:
        iou=f"{p['failure_iou']:.3f}" if p["failure_iou"] is not None else "No positive union"
        lines.append(f"| {p['episode']} | {p['left']} / {p['right']} | {100*p['frame_agreement']:.2f}% | {iou} |")
    if result["invalid"]:
        lines += ["", "## Stopped outputs", ""] + ["- "+x["trace"]+": "+x["error"] for x in result["invalid"]]
    lines += ["", "Review the original videos and every repeat before treating these proposals as training labels."]
    (root/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return result


def review(root, supplement_runs=None):
    """Combine compatible disjoint runs without regenerating or rewriting labels."""
    root=Path(root).resolve(); m=verify(root)
    sources=[(root,m,validate(root))]
    for source in supplement_runs or []:
        source=Path(source).resolve(); extra=verify(source)
        settings=("evidence","max_image_side","teachers","repeats","reasoning","max_input_tokens","max_output_tokens")
        if ((m["repo"],m["revision"],m.get("source_manifest_sha256")) !=
            (extra["repo"],extra["revision"],extra.get("source_manifest_sha256")) or
            common.sha(root/"prompt.md") != common.sha(source/"prompt.md") or
            m['config'].get('camera_layout', 'separate_images') != extra['config'].get('camera_layout', 'separate_images') or
            any(m["config"][k] != extra["config"][k] for k in settings)):
            raise ValueError("Combined V9 review requires the same prompt and evidence protocol")
        sources.append((source,extra,validate(source)))
    data=dict(protocol=PROTOCOL, prompt_revision=m["config"].get("prompt_revision", "v9"), manifest_sha256=common.sha(root/"manifest.json"), episodes=[])
    seen=set(); rows=[]; errors=[]

    def review_copy(source, relative):
        destination=common.inside(root,relative)
        destination.parent.mkdir(parents=True,exist_ok=True)
        if not destination.exists():
            try: os.link(source,destination)
            except OSError: shutil.copyfile(source,destination)
        if common.sha(source) != common.sha(destination):
            raise ValueError("A review copy differs from its preserved original")
        return relative

    for source,manifest,result in sources:
        errors.extend(result["invalid"])
        for e in manifest["episodes"]:
            if e["id"] in seen:
                raise ValueError("Duplicate episode across combined review sources")
            seen.add(e["id"])
            videos=[]
            for v in e["videos"]:
                url=v["url"] if source==root else review_copy(common.inside(source,v["url"]),f"review_media/{source.name}/{v['url']}")
                videos.append(dict(v,url=url))
            traces={t:[] for t in manifest["config"]["teachers"]}
            for row in result["traces"]:
                if row["episode"] != e["id"]: continue
                relative=f"traces/{trace_name(e['id'],row['teacher'],row['repeat'])}/annotation.md"
                if source!=root:
                    relative=review_copy(common.inside(source,relative),f"review_annotations/{source.name}/{relative}")
                traces[row["teacher"]].append(dict(repeat=row["repeat"],segments=row["segments"],markdown=relative))
                rows.append((e,row,source.name))
            data["episodes"].append(dict(id=e["id"],task=e["task"],split=e["split"],lab=e["lab"],fps=e["fps"],n_frames=e["n_frames"],
                videos=videos,teachers=traces,source_run=source.name,source_manifest_sha256=common.sha(source/"manifest.json")))
    data["episodes"].sort(key=lambda e:e["id"])
    data['planned_responses'] = sum(result['planned'] for _, _, result in sources)
    data['repeats'] = m['config']['repeats']
    data['review_ui_version'] = common.sha(Path(__file__).with_name('binary_segments_v9_review.html'))
    template=Path(__file__).with_name("binary_segments_v9_review.html").read_text(encoding="utf-8")
    revision = m['config'].get('prompt_revision', 'v9').upper()
    template = template.replace('V9 binary failure review', revision+' binary failure review')
    template = template.replace('V9 · Failure or non-failure', revision+' · Failure or non-failure')
    template = template.replace('V9 video review', revision+' video review')
    if supplement_runs:
        template=template.replace('href="report.md"','href="review_report.md"')
    embedded=json.dumps(data,ensure_ascii=False).replace("<","\\u003c").replace("\u2028","\\u2028").replace("\u2029","\\u2029")
    def publish(name, text):
        target = root/name
        temporary = root/(name+'.'+uuid.uuid4().hex+'.tmp')
        temporary.write_text(text,encoding='utf-8')
        temporary.replace(target)
    # Publish the complete page before advertising its UI version to live tabs.
    publish('review.html',template.replace('__DATA__',embedded))
    publish('review_data.json',json.dumps(data,ensure_ascii=False)+'\n')
    lines=["# Combined binary V9 video review","",f"- Episodes: {len(seen)}. Validated teacher responses: {len(rows)}.",
        "- Original prompt, complete recorded-frame evidence, camera identities and split assignments are preserved.",
        "- Earlier annotations are byte-identical review copies, not new teacher calls.",
        "- Teacher proposals require video review; repeat agreement is not accuracy.","",
        "| Episode | Teacher | Repeat | Failure intervals (seconds) | Source run |","| --- | --- | ---: | --- | --- |"]
    for e,row,source in sorted(rows,key=lambda x:(x[0]["id"],x[1]["teacher"],x[1]["repeat"])):
        intervals=", ".join(f"{s['start_frame']/e['fps']:.2f}–{s['end_frame']/e['fps']:.2f}" for s in row["segments"] if s["failure"]) or "None proposed"
        lines.append(f"| {e['id']} | {row['teacher'].title()} | {row['repeat']} | {intervals} | {source} |")
    (root/"review_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return dict(review=str(root/"review.html"),episodes=len(seen),validated=len(rows),invalid=errors)


def main():
    ap=argparse.ArgumentParser(description=__doc__); subs=ap.add_subparsers(dest="command",required=True)
    p=subs.add_parser("prepare"); p.add_argument("--config",type=Path,default=common.ROOT/"configs/oopsie_binary_v9.json")
    for name in ("verify","preflight","collect","validate","report","review"):
        p=subs.add_parser(name); p.add_argument("--run",type=Path,required=True)
        if name=="collect": p.add_argument("--budget-usd",type=float,required=True)
        if name=="review": p.add_argument("--supplement-run",type=Path,action="append")
    args=ap.parse_args()
    if args.command=="prepare": result=prepare(args.config)
    elif args.command=="verify": result=dict(frozen_inputs_valid=True,episodes=len(verify(args.run)["episodes"]))
    elif args.command=="collect": result=collect(args.run,args.budget_usd)
    elif args.command=="review": result=review(args.run,args.supplement_run)
    else: result=globals()[args.command](args.run)
    print(json.dumps(result,indent=2))
    if result.get("invalid"): raise SystemExit(1)


if __name__=="__main__":
    main()
