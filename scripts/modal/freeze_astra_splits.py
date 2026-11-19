"""Freeze episode-level train, development, and test splits without reading labels."""
import argparse
from collections import defaultdict
import json
from pathlib import Path, PurePosixPath
import random
import re

from prepare_astra_pilot import EXCLUDED, SEED, digest, read

HOLDOUT_LABS = {"UW_REAL", "UofT_RVL"}


def components(catalog, selection):
    owners = {}
    parents = {episode["id"]: episode["id"] for episode in catalog}

    def root(eid):
        while parents[eid] != eid:
            parents[eid] = parents[parents[eid]]
            eid = parents[eid]
        return eid

    for episode in catalog:
        eid = episode["id"]
        lab = episode["lab"]
        task = re.sub(r"[^\w]+", " ", episode["task"].casefold()).strip()
        folder = PurePosixPath(selection[eid]["release_path"]).parts[2:-1]
        keys = [("task", lab, task), *(("video", video["sha256"]) for video in episode["videos"])]
        if folder:
            keys.append(("collection", lab, folder))
        for key in keys:
            parents[root(eid)] = root(owners.setdefault(key, eid))

    groups = defaultdict(list)
    for eid in sorted(parents):
        groups[root(eid)].append(eid)
    return list(groups.values())


def fill_groups(groups, target):
    """Pick whole groups close to target, preferring undershoot on a tie."""
    paths = {0: ()}
    for group in groups:
        size = len(group)
        for count, previous in list(paths.items()):
            paths.setdefault(count + size, (*previous, group))
        if target in paths:
            return list(paths[target])
    closest = min(paths, key=lambda count: (abs(count - target), count))
    return list(paths[closest])


def freeze(export, pilot, output):
    catalog = read(export / "catalog.json")
    selection = {episode["id"]: episode for episode in read(export / "selection.json")["episodes"]}
    manifest = read(export / "EXPORT_MANIFEST.json")["files"]
    for name in ("catalog.json", "selection.json"):
        if digest(export / name) != manifest[name]:
            raise ValueError(f"Pinned export changed: {name}")
    episodes = {episode["id"]: episode for episode in catalog}
    groups = components(catalog, selection)
    training_pilot = {w["episode"] for w in read(pilot)["windows"] if w["split"] == "train"}
    pinned = training_pilot | EXCLUDED
    rng = random.Random(SEED)
    rng.shuffle(groups)
    lab_test = [group for group in groups if any(episodes[eid]["lab"] in HOLDOUT_LABS for eid in group)]
    if any(pinned.intersection(group) for group in lab_test):
        raise ValueError("Lab holdout overlaps a training or debug episode")
    eligible = [group for group in groups if group not in lab_test and not pinned.intersection(group)]
    task_test = fill_groups(eligible, 200 - sum(map(len, lab_test)))
    development = fill_groups([g for g in eligible if g not in task_test], 100)

    folds = {}
    for group in groups:
        if group in lab_test:
            split, stratum = "test", "unseen_lab"
        elif group in task_test:
            split, stratum = "test", "unseen_collection_or_task_at_lab"
        elif group in development:
            split, stratum = "development", None
        else:
            split, stratum = "train", None
        for eid in group:
            folds[eid] = dict(split=split, group=group[0], stratum=stratum)
    counts = {split: sum(row["split"] == split for row in folds.values())
              for split in ("train", "development", "test")}
    payload = dict(counts=counts, source_manifest_sha256=digest(export / "EXPORT_MANIFEST.json"),
                   seed=SEED, heldout_labs=sorted(HOLDOUT_LABS), folds=folds)
    contents = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
    if output.exists() and output.read_bytes() != contents:
        raise ValueError("Refusing to replace the frozen split")
    output.write_bytes(contents)
    print(f"Frozen folds {counts}, including {sum(map(len, lab_test))} unseen-lab test episodes")
    print(f"Split SHA-256 {digest(output)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("initial_pilot", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    freeze(args.export, args.initial_pilot, args.output)
