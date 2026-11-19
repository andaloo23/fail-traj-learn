"""Stage a reproducible pilot from the frozen labels and prepared camera strips."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "distill"))
from qwen_backbone_timing import MODELS, digest, read, targets

SEED = 20261118
EXCLUDED = {"C0052", "C0079", "C0188"}
REMOTE = (
    "/C:/Users/LocalPC/dev/fail-traj-learn/outputs/"
    "corral_astra_rich_failure_v8_2_carryforward_batch_v3"
)


def copy_missing(host, remote, paths):
    missing = {dest: source for source, dest in paths if not dest.is_file()}
    if not missing:
        return
    commands = []
    for dest, source in missing.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        commands.append(f'get "{remote}/{source}" "{dest}.part"')
    subprocess.run(["sftp", "-q", "-b", "-", host], input="\n".join(commands) + "\n",
                   text=True, check=True, stdout=subprocess.DEVNULL)
    for dest in missing:
        dest.with_name(dest.name + ".part").replace(dest)


def copy_frame_archive(host, remote, output, files):
    pending = {path for path in files if not (output / path).is_file()}
    if not pending:
        return
    # A single archive avoids a Windows SFTP round trip for each camera strip.
    windows = "C:/Users/LocalPC/AppData/Local/Temp"
    stem = f"{windows}/qwen-astra-{uuid4().hex}"
    with TemporaryDirectory() as staging:
        stage = Path(staging)
        manifest = stage / "paths.txt"
        manifest.write_text("\n".join(sorted(pending)) + "\n", encoding="utf-8")
        download = stage / "frames.tar"
        try:
            subprocess.run(["scp", "-q", str(manifest), f"{host}:{stem}.txt"], check=True)
            subprocess.run(["ssh", "-o", "BatchMode=yes", host,
                            f"tar.exe -C '{remote.removeprefix('/')}' -cf '{stem}.tar' -T '{stem}.txt'"],
                           check=True)
            subprocess.run(["scp", "-q", f"{host}:{stem}.tar", str(download)], check=True)
        finally:
            subprocess.run(["ssh", "-o", "BatchMode=yes", host,
                            f"Remove-Item -LiteralPath '{stem}.txt','{stem}.tar' -ErrorAction SilentlyContinue"],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with tarfile.open(download, "r|") as archive:
            for member in archive:
                if member.name not in pending or not member.isfile():
                    raise ValueError(f"Unexpected Windows archive entry: {member.name}")
                destination = output / member.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                temp = destination.with_suffix(".webp.part")
                with archive.extractfile(member) as stream:
                    temp.write_bytes(stream.read())
                temp.replace(destination)
                pending.remove(member.name)
        if pending:
            raise ValueError(f"The Windows archive omitted {len(pending)} requested frames")


def select(export, development_ids=None):
    initial_train = []
    if development_ids is not None:
        initial_train = [row for row in select(export) if row[1] == "train"]
    catalog = read(export / "catalog.json")
    assert len(catalog) == 1000
    manifest = read(export / "EXPORT_MANIFEST.json")["files"]
    assert digest(export / "catalog.json") == manifest["catalog.json"]
    rng = random.Random(SEED)
    rng.shuffle(catalog)
    used = {video["sha256"] for episode, *_ in initial_train for video in episode["videos"]}
    counts = {("train", False): 15, ("train", True): 35,
              ("development", False): 3, ("development", True): 7}
    if development_ids is not None:
        counts["train", False] = counts["train", True] = 0
    selected = initial_train[:]
    for episode in catalog:
        eid = episode["id"]
        hashes = {video["sha256"] for video in episode["videos"]}
        if eid in EXCLUDED or used & hashes or development_ids is not None and eid not in development_ids:
            continue
        ref = f"canonical/{eid}_final/parsed.json"
        assert digest(export / ref) == manifest[ref]
        parsed = read(export / ref)
        annotations = parsed["failure_annotations"]
        split = next((split for split in ("development", "train")
                      if counts[split, bool(annotations)] > 0), None)
        if split is None:
            continue
        count = min(64, episode["n_frames"])
        if annotations:
            event = min(annotations, key=lambda item: item["end_frame"] - item["start_frame"])
            center = (event["start_frame"] + event["end_frame"]) // 2
            start = min(max(0, center - count // 2), episode["n_frames"] - count)
        else:
            start = rng.randrange(episode["n_frames"] - count + 1)
        selected.append((episode, split, parsed, start, count, manifest[ref]))
        used.update(hashes)
        counts[split, bool(annotations)] -= 1
        if not any(counts.values()):
            return selected
    raise ValueError(f"Could not select disjoint pilot episodes: {counts}")


def prepare(export, output, host, splits=None, *, selected=None, conservative=False):
    source_hash = digest(export / "EXPORT_MANIFEST.json")
    development_ids = None
    if splits is not None:
        frozen = read(splits)
        if frozen["source_manifest_sha256"] != source_hash:
            raise ValueError("Split manifest uses a different label export")
        development_ids = {eid for eid, row in frozen["folds"].items() if row["split"] == "development"}
    if selected is None:
        selected = select(export, development_ids)
    media = output.parent / "media"
    copy_missing(host, REMOTE, [(f"prepared/{e['id']}.json", media / f"{e['id']}.json")
                                for e, *_ in selected])
    windows = []
    for episode, split, parsed, start, count, parsed_hash in selected:
        eid = episode["id"]
        if splits is not None and frozen["folds"][eid]["split"] != split:
            raise ValueError(f"Pilot episode crosses the frozen split: {eid}")
        prepared = read(media / f"{eid}.json")
        assert all(prepared[key] == episode[key] for key in ("id", "task", "fps", "n_frames", "videos"))
        images = prepared["images"][start:start + count]
        assert [row["frame"] for row in images] == list(range(start, start + count))
        assert all(row["path"] == f"images/{eid}/{row['frame']:06d}.webp" for row in images)
        cameras = ", ".join(panel["camera"] for panel in images[0]["panels"])
        stop = start + count
        prompt = (
            f"Task: {episode['task']}\n"
            f"Camera panels from left to right: {cameras}. Native FPS: {episode['fps']}.\n"
            f"Label every frame in the supplied interval [{start}, {stop}) using global frame indices. "
            "End indices are exclusive. Preserve distinct adjacent failures. Return Markdown only.\n\n"
            "# Failure segments\n\n"
            "| Start frame | End frame (exclusive) | Failure |\n|---|---|---|\n"
            "Use Yes or No in the Failure column. Then provide a second table. Include categories and "
            "explanations only for wholly visible failure events. Leave this table empty when there are none.\n\n"
            "# Visible failure details\n\n"
            "| Start frame | End frame (exclusive) | Categories | Explanation |\n|---|---|---|---|"
        )
        if conservative:
            prompt += (
                "\nMark a failure only when the video shows an unsuccessful action, unintended physical "
                "effect, or observable failure to progress. A clip can end before task completion "
                "without showing any failure. Ground each explanation in a named camera and source frames."
            )
        windows.append(dict(id=f"{eid}_{start}_{count}", episode=eid, split=split,
                            start=start, count=count, fps=episode["fps"], task=episode["task"],
                            episode_frames=episode["n_frames"], images=images, prompt=prompt,
                            parsed_sha256=parsed_hash,
                            has_failure=any(s["failure"] and s["start_frame"] < stop and s["end_frame"] > start
                                            for s in parsed["segments"]),
                            targets={"SCE": targets(parsed, start, stop, require_details=False)["SCE"]}))
    files = {row["path"]: row["sha256"] for window in windows for row in window["images"]}
    image_root = REMOTE.replace("carryforward_batch_v3", "1000_batch_v2")
    for path in files:
        prior = next((output.parent / name / path for name in ("pilot-grouped", "pilot")
                      if (output.parent / name / path).is_file()), None)
        destination = output / path
        if prior is not None and not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.hardlink_to(prior)
    copy_frame_archive(host, image_root, output, files)
    for path, expected in files.items():
        if digest(output / path) != expected:
            raise ValueError(f"Prepared camera strip checksum mismatch: {path}")
    plan = dict(model=MODELS["candidate"], seed=SEED, source="Astra V8.2 portable export",
                export_manifest_sha256=source_hash, windows=windows)
    if splits is not None:
        plan["split_manifest_sha256"] = digest(splits)
    encoded = (json.dumps(plan, ensure_ascii=False, indent=2) + "\n").encode()
    dest = output / "plan.json"
    if dest.exists() and dest.read_bytes() != encoded:
        raise ValueError("The prepared pilot plan already exists with different content")
    dest.write_bytes(encoded)
    packed = output.parent / f"{output.name}-frames.tar"
    partial = packed.with_suffix(".tar.part")
    with tarfile.open(partial, "w") as archive:
        for path in sorted(files):
            archive.add(output / path, arcname=path, recursive=False)
    partial.replace(packed)
    print(f"Prepared {len(windows)} disjoint episode windows and {len(files)} checksummed frames.")
    print(f"Pilot SHA-256: {hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--host", default="local-pc")
    parser.add_argument("--splits", type=Path)
    args = parser.parse_args()
    prepare(args.export.resolve(), args.output.resolve(), args.host, args.splits)
