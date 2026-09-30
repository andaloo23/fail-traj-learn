#!/usr/bin/env python3
"""Launch a candidate-assisted review of the GPT-6 v3 review pack.

Examples:
  python scripts/annotate/launch_gpt6_v3_review.py \\
      ~/Downloads/gpt6_v3_12_episode_review_pack.zip --reviewer alice

  python scripts/annotate/launch_gpt6_v3_review.py \\
      ~/Downloads/gpt6_v3_12_episode_review_pack --reviewer alice
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path


PACK_NAME = "gpt6_v3_12_episode_review_pack"
CANDIDATE_NAME = "gpt6_fewshot_v3_annotation.json"


def extract_pack(archive: Path) -> Path:
    destination = archive.with_suffix("")
    if destination.is_dir():
        return destination
    with zipfile.ZipFile(archive) as bundle:
        destination_resolved = destination.resolve()
        for member in bundle.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination_resolved):
                raise ValueError(f"archive contains an unsafe path: {member.filename}")
        bundle.extractall(destination.parent)
    return destination


def review_sources(pack: Path) -> Path:
    episodes = pack / "episodes"
    ids = [f"R{i:03d}" for i in range(1, 13)]
    missing = [
        str(episodes / episode / name)
        for episode in ids
        for name in ("cameras.npz", CANDIDATE_NAME)
        if not (episodes / episode / name).is_file()
    ]
    if missing:
        raise ValueError(
            "This is not a complete GPT-6 v3 review pack; missing " + ", ".join(missing[:3])
        )
    return episodes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path, help="Review-pack directory or its .zip archive")
    parser.add_argument("--reviewer",
                        help="Optional name used only when you intend to save a separate review")
    parser.add_argument("--no-browser", action="store_true", help="Print the local URL without opening it")
    args = parser.parse_args()

    if args.reviewer is not None and not re.fullmatch(r"[A-Za-z0-9_-]+", args.reviewer):
        parser.error("--reviewer may contain letters, digits, underscores, and hyphens only")

    pack = args.pack.expanduser().resolve()
    if pack.suffix.lower() == ".zip":
        if not pack.is_file():
            parser.error(f"archive does not exist: {pack}")
        try:
            pack = extract_pack(pack)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            parser.error(str(exc))
    elif not pack.is_dir():
        parser.error(f"pack directory does not exist: {pack}")

    if pack.name != PACK_NAME:
        candidate = pack / PACK_NAME
        if candidate.is_dir():
            pack = candidate
    try:
        episodes = review_sources(pack)
    except ValueError as exc:
        parser.error(str(exc))

    script = Path(__file__).with_name("human_annotator.py")
    annotation_name = (
        f"review_{args.reviewer}.json" if args.reviewer else "review_preview.json"
    )
    command = [
        sys.executable, str(script), str(episodes),
        "--seed-name", CANDIDATE_NAME,
        "--annotation-name", annotation_name,
    ]
    if args.no_browser:
        command.append("--no-browser")
    print(f"Opening 12 GPT-6 candidate annotations from {pack}")
    if args.reviewer:
        print(f"Your separate review files will be named {annotation_name}")
    else:
        print("Viewing GPT labels. No file is written unless you choose Save in the editor.")
    try:
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        print("\nViewer stopped.")


if __name__ == "__main__":
    main()
