"""Build synced original-video review with readable annotations and Markdown notes."""
import argparse
import json
import os
from pathlib import Path
import shutil

import oopsie_common as common
import oopsie_markdown


def compatible_episodes(left, right):
    if (left["repo"], left["revision"]) != (right["repo"], right["revision"]):
        raise ValueError("Review supplements must use the same source release")
    a, b = ({e["id"]: e for e in m["episodes"]} for m in (left, right))
    if a.keys() != b.keys():
        raise ValueError("Review supplements must have identical episode identities")
    for eid, episode in a.items():
        other = b[eid]
        for key in ("release_path", "task", "split", "n_frames", "fps", "sampled_frames"):
            if episode[key] != other[key]:
                raise ValueError("Review supplement has different source evidence or splits")
        for key in ("cameras", "original_cameras"):
            if episode[key] != other[key]:
                raise ValueError("Review supplement uses different native cameras")


def build(root, supplement_run=None):
    root = Path(root).resolve()
    manifest = common.verify(root)
    from oopsie_pipeline import validate
    checked = validate(root)
    sources = [(root, manifest, checked)]
    for extra in ([supplement_run] if isinstance(supplement_run, (str, Path)) else supplement_run or []):
        extra = Path(extra).resolve()
        extra_manifest = common.verify(extra)
        compatible_episodes(manifest, extra_manifest)
        sources.append((extra, extra_manifest, validate(extra)))
    source = common.inside(common.ROOT, manifest["config"]["source"]) / "source"
    episodes = []
    for episode in manifest["episodes"]:
        # Keep both teachers for an episode on one source protocol. An approved
        # primary episode is never replaced by a new-format supplement.
        selected_root, selected_manifest, selected_checked = sources[0]
        for candidate_root, candidate_manifest, candidate_checked in sources:
            invalid_candidates = {r["trace"] for r in candidate_checked["invalid"]}
            ready = False
            for teacher in candidate_manifest["config"]["teachers"]:
                stem = episode["id"] + "_" + teacher
                attempt_path = candidate_root / "traces" / stem / "attempt.json"
                if attempt_path.exists() and common.read(attempt_path).get("status") == "validated" and stem not in invalid_candidates:
                    ready = True
            if ready:
                selected_root, selected_manifest, selected_checked = candidate_root, candidate_manifest, candidate_checked
                break
        invalid = {row["trace"] for row in selected_checked["invalid"]}
        videos = []
        original = {c["camera"]: c for c in episode["original_cameras"]}
        for index, camera in enumerate(episode["cameras"]):
            info = original[camera["camera"]]
            src = common.inside(source, info["path"])
            if common.sha(src) != info["sha256"]:
                raise ValueError("Original review video changed from its audited bytes")
            relative = f"videos/{episode['id']}/{index:02d}.mp4"
            destination = common.inside(root, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                try:
                    os.link(src, destination)
                except OSError:
                    shutil.copyfile(src, destination)
            if common.sha(destination) != info["sha256"]:
                raise ValueError("Review copy differs from original audited video")
            videos.append(dict(camera=camera["camera"], description=camera["description"], url=relative))
        teachers = {}
        for teacher in manifest["config"]["teachers"]:
            folder = selected_root / "traces" / (episode["id"] + "_" + teacher)
            attempt = common.read(folder / "attempt.json") if (folder / "attempt.json").exists() else {}
            if attempt.get("status") != "validated" or episode["id"] + "_" + teacher in invalid:
                teachers[teacher] = dict(status="pending" if not attempt or attempt.get("status") == "in_flight" else "unavailable")
                continue
            value = common.load_annotation(folder, selected_manifest)
            common.validate_annotation(value, episode)
            relative = f"annotations/{episode['id']}_{teacher}.md"
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            native = common.annotation_format(selected_manifest) == "markdown"
            if native:
                text = common.annotation_path(folder, selected_manifest).read_bytes().decode("utf-8")
            else:
                text = oopsie_markdown.render(value)
                text += ("\n<!-- Readable Markdown conversion of the preserved original teacher output. "
                         "This was not generated natively in Markdown. -->\n")
            path.write_bytes(text.encode("utf-8"))
            teachers[teacher] = dict(status="ready", annotation=value, markdown=relative,
                                     native_markdown=native)
        episodes.append(dict(id=episode["id"], task=episode["task"], lab=episode["lab"], split=episode["split"],
                             fps=episode["fps"], n_frames=episode["n_frames"], sampled_frames=episode["sampled_frames"],
                             source_manifest_sha256=common.sha(selected_root / "manifest.json"),
                             source_run=selected_root.name,
                             videos=videos, teachers=teachers))
        if "window_start_frame" in episode:
            episodes[-1].update({k: episode[k] for k in ("source_episode_id", "window_start_frame", "window_end_frame")})
    data = dict(episodes=episodes, manifest_sha256=common.sha(root / "manifest.json"),
                ready_episodes=sum(any(t["status"] == "ready" for t in e["teachers"].values()) for e in episodes))
    template = Path(__file__).with_name("oopsie_video_review.html").read_text(encoding="utf-8")
    embedded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    (root / "review.html").write_text(template.replace("__DATA__", embedded), encoding="utf-8")
    (root / "video_review.md").write_text(
        "# OopsieData video review\n\nOpen `review.html` through the local video server.\n\n"
        "Play the original synced cameras, scrub/step frames, and compare time-aligned Sol/Astra descriptions. "
        "Evidence links jump to the cited observation. Record review decisions and corrections in Markdown.\n\n"
        "Full videos include observations the teachers were not supplied. The interface identifies sampled frames. "
        "Teacher-assisted review notes do not automatically change annotations, uncertainty masks, or reference status.\n",
        encoding="utf-8")
    (root / "video_sources.md").write_text(
        "# Video review label sources\n\nPrimary episodes retain their original teacher protocol. "
        "Supplementary labels keep their own frozen manifest and original outputs.\n\n"
        "| Episode | Label source | Sol | Astra |\n| --- | --- | --- | --- |\n" +
        "\n".join(f"| {e['id']} | {e['source_run']} | {e['teachers']['sol']['status']} | {e['teachers']['astra']['status']} |" for e in episodes) + "\n",
        encoding="utf-8")
    ready = sum(t["status"] == "ready" for e in episodes for t in e["teachers"].values())
    return dict(review=str(root / "review.html"), videos=sum(len(e["videos"]) for e in episodes),
                ready_episodes=data["ready_episodes"], displayed_validated_traces=ready,
                displayed_planned_traces=sum(len(e["teachers"]) for e in episodes),
                generation_estimate_usd=sum(s[2]["generation_estimate_usd"] for s in sources),
                label_sources=[str(s[0]) for s in sources])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--supplement-run", type=Path, action="append")
    args = parser.parse_args()
    print(json.dumps(build(args.run, args.supplement_run), indent=2))
