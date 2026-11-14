"""Portable contracts for real OopsieData distillation; no simulation defaults."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/annotate"))
from annotate_trajectories import validate_atomic
from export_distillation_v8 import target_with_masks as json_target_with_masks
import oopsie_markdown

REPO_ID = "OopsieData-Submissions/oopsiedata-v0.1"


def annotation_format(manifest):
    return manifest["config"].get("annotation_format", "json")


def parse_answer(text, format="json"):
    if format == "markdown":
        return oopsie_markdown.parse(text)[0]
    if format != "json":
        raise ValueError("Unknown annotation format")
    return json.loads(text)


def target_with_masks(value, format="json", text=None):
    if format == "markdown":
        return oopsie_markdown.target_with_masks(value, text)
    if format != "json":
        raise ValueError("Unknown annotation format")
    return json_target_with_masks(value)


def annotation_path(folder, manifest):
    return Path(folder) / ("annotation.md" if annotation_format(manifest) == "markdown" else "annotation.json")


def load_annotation(folder, manifest):
    return parse_answer(annotation_path(folder, manifest).read_bytes().decode("utf-8"), annotation_format(manifest))


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def sha(path):
    with Path(path).open("rb") as stream:
        if hasattr(hashlib,'file_digest'):
            return hashlib.file_digest(stream, "sha256").hexdigest()
        digest=hashlib.sha256()
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
        return digest.hexdigest()


def inside(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path escapes artifact root: {relative}")
    return path


def validate_annotation(value, episode):
    """Keep original native camera IDs; reuse the frozen V8 partition checks.

    The legacy validator only accepts agent/wrist. Validate native pairs first,
    then map a private copy for its camera-independent action/partition checks.
    Neither the original annotation nor historical V8 code is modified.
    """
    if not isinstance(value, dict) or not isinstance(value.get("segments"), list) or not isinstance(value.get("identity_check"), dict):
        raise ValueError("Expected an annotation object, identity object, and segment array")
    allowed = {(s["frame"], s["camera"]) for s in episode["images"]}
    cloned = copy.deepcopy(value)
    v3 = episode.get("annotation_schema") == "field_review_v3"
    for original, segment in zip(value["segments"], cloned["segments"]):
        if ("uncertain_fields" in segment) != v3:
            raise ValueError("Annotation uncertainty schema differs from the frozen episode")
        if v3:
            oopsie_markdown.field_masks(original)
            if original["action"] == "unknown" and "action" not in original["uncertain_fields"]:
                raise ValueError("Unknown operation requires action uncertainty")
            segment.pop("uncertain_fields")
    groups = [cloned.get("identity_check", {})] + cloned.get("segments", [])
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("evidence"), list):
            raise ValueError("Every identity/segment needs an evidence array")
        for item in group.get("evidence", []):
            if not isinstance(item, dict):
                raise ValueError("Evidence entries must be objects")
            if (item.get("frame"), item.get("camera")) not in allowed:
                raise ValueError("Evidence cites an unsupplied native frame/camera pair")
            item["camera"] = "agent"
    start, end = episode.get("window_start_frame", 0), episode.get("window_end_frame", episode["n_frames"])
    validation_episode = dict(episode, n_frames=end-start, sampled_frames=[f-start for f in episode["sampled_frames"]])
    for group in groups:
        for item in group["evidence"]:
            item["frame"] -= start
    for segment in cloned["segments"]:
        segment["start_frame"] -= start
        segment["end_frame"] -= start
    validate_atomic(cloned, validation_episode, label_mode="failure_binary")
    supplied = set(episode["sampled_frames"])
    previous = None
    for segment in value["segments"]:
        new_positive = segment["failure"] and (
            previous is None or not previous["failure"] or
            not set(segment["categories"]) <= set(previous["categories"]))
        if new_positive and segment["start_frame"] not in supplied:
            raise ValueError("Positive failure onset must be a supplied frame")
        previous = segment


def messages(root, manifest, episode):
    metadata = {k: episode[k] for k in ("id", "task", "n_frames", "fps", "sampled_frames", "cameras")}
    metadata["episode_id"] = metadata.pop("id")
    prompt = inside(root, "prompt.txt").read_text(encoding="utf-8")
    markdown = annotation_format(manifest) == "markdown"
    if markdown:
        info = (f"## Episode input\n\n- Episode: {episode['id']}\n- Task: {episode['task']}\n"
                f"- Source frames: {episode['n_frames']}\n- Frames per second: {episode['fps']}\n"
                f"- Supplied frames: {', '.join(map(str, episode['sampled_frames']))}\n\n### Cameras\n\n" +
                "\n".join(f"- {c['camera']}: {c['description']}" for c in episode["cameras"]))
        if "window_start_frame" in episode:
            info += (f"\n\n- Source episode: {episode['source_episode_id']}"
                     f"\n- Window frames: {episode['window_start_frame']}–{episode['window_end_frame']} (end exclusive)"
                     "\n- Annotate only this window using original source frame indices. Outside-window observations are not supplied.")
    else:
        info = json.dumps(metadata, ensure_ascii=False)
    content = [{"type": "text", "text": prompt + "\n" + info}]
    for item in episode["images"]:
        label = f"### Frame {item['frame']} · {item['seconds']:.6f} seconds · camera {item['camera']}" if markdown else json.dumps({k: item[k] for k in ("frame", "seconds", "camera")})
        content.append({"type": "text", "text": label})
        content.append({"type": "image", "image": item["path"]})
    return [{"role": "user", "content": content}]


def verify(root):
    root = Path(root)
    manifest = read(root / "manifest.json")
    if manifest["format"] != "oopsie_distillation_v1" or manifest["repo"] != REPO_ID:
        raise ValueError("Only the frozen real OopsieData format is accepted")
    if manifest.get("source_annotations_used_as_model_input", False):
        raise ValueError("Source annotations must be excluded from model inputs")
    for name, digest in manifest["files"].items():
        if sha(inside(root, name)) != digest:
            raise ValueError(f"Changed frozen input: {name}")
    identities, split_labs, source_splits, split_ids = set(), {}, {}, {k: set() for k in ("train", "development", "test")}
    for episode in manifest["episodes"]:
        start, end = episode.get("window_start_frame", 0), episode.get("window_end_frame", episode["n_frames"])
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= episode["n_frames"]:
            raise ValueError("Invalid source window")
        source_key = (manifest["repo"], manifest["revision"], episode["release_path"])
        key = source_key + (start, end)
        if key in identities:
            raise ValueError("Duplicate source episode identity")
        identities.add(key)
        if source_key in source_splits and source_splits[source_key] != episode["split"]:
            raise ValueError("Related source windows cross splits")
        source_splits[source_key] = episode["split"]
        if episode.get("annotation_schema") != manifest["config"].get("annotation_schema"):
            raise ValueError("Episode and frozen annotation schemas differ")
        if episode["id"] in set.union(*split_ids.values()):
            raise ValueError("Duplicate episode ID")
        split_ids[episode["split"]].add(episode["id"])
        lab = episode["lab"]
        if lab in split_labs and split_labs[lab] != episode["split"]:
            raise ValueError("Lab crosses frozen splits")
        split_labs[lab] = episode["split"]
        images = episode["images"]
        if not images or {x["path"] for x in images} - manifest["files"].keys():
            raise ValueError("Unhashed or missing images")
        if episode["sampled_frames"] != sorted({x["frame"] for x in images}):
            raise ValueError("Sampled-frame manifest differs from images")
        for camera in episode["cameras"]:
            frames = [x["frame"] for x in images if x["camera"] == camera["camera"]]
            if frames != episode["sampled_frames"]:
                raise ValueError("Incomplete camera evidence")
        if episode["sampled_frames"][0] != start or episode["sampled_frames"][-1] != end - 1:
            raise ValueError("First/final frames must be supplied")
        if any(not start <= f < end for f in episode["sampled_frames"]):
            raise ValueError("Sampled evidence lies outside its window")
    if not all(split_ids.values()):
        raise ValueError("Train, development, and test must each contain episodes")
    return manifest


def load_export(path, split="train"):
    path = Path(path)
    receipt = read(path / "export.json")
    root = (path / receipt["run"]).resolve()
    manifest = verify(root)
    if sha(root / "manifest.json") != receipt["manifest_sha256"]:
        raise ValueError("Export points at a different frozen run")
    episodes = {e["id"]: e for e in manifest["episodes"]}
    records = []
    seen = set()
    for name, digest in receipt["files"].items():
        if sha(inside(path, name)) != digest:
            raise ValueError(f"Changed export file: {name}")
    with (path / (split + ".jsonl")).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["episode_id"] in seen:
                raise ValueError("An episode cannot be duplicated in the same training export")
            seen.add(row["episode_id"])
            episode = episodes[row["episode_id"]]
            if row["split"] != split or episode["split"] != split:
                raise ValueError("Split leakage in training export")
            format = annotation_format(manifest)
            if row.get("target_format", format) != format:
                raise ValueError("Target format differs from the frozen run")
            value = parse_answer(row["messages"][-1]["content"], format)
            validate_annotation(value, episode)
            text, supervision = target_with_masks(value, format, row["messages"][-1]["content"])
            if row["messages"][-1]["content"] != text or row["supervision"] != supervision:
                raise ValueError("Target or uncertainty masks changed")
            if row["messages"][:-1] != messages(root, manifest, episode):
                raise ValueError("Student evidence differs from frozen teacher input")
            records.append(row)
    return root, manifest, records
