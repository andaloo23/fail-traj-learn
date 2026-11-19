"""Select masked, same-task test pairs for independent video annotation."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import re

from prepare_astra_pilot import SEED, digest, read

PAIR_COUNTS = {"unseen_lab": 8, "unseen_collection_or_task_at_lab": 16}


def freeze_challenge(export, splits, output):
    split = read(splits)
    if split["source_manifest_sha256"] != digest(export / "EXPORT_MANIFEST.json"):
        raise ValueError("Split and challenge exports differ")
    pinned = read(export / "EXPORT_MANIFEST.json")["files"]
    catalog = read(export / "catalog.json")
    candidates = defaultdict(lambda: defaultdict(list))
    for episode in catalog:
        eid = episode["id"]
        fold = split["folds"][eid]
        if fold["split"] != "test":
            continue
        relative = f"canonical/{eid}_final/parsed.json"
        if digest(export / relative) != pinned[relative]:
            raise ValueError(f"Changed reference for {eid}")
        outcome = read(export / relative)["success_label"]
        if outcome in {"failure", "success"}:
            key = (fold["stratum"], episode["lab"],
                   re.sub(r"[^\w]+", " ", episode["task"].casefold()).strip(),
                   tuple(video["camera"] for video in episode["videos"]))
            candidates[key][outcome].append(episode)

    matched = defaultdict(list)
    for (stratum, *_), outcomes in candidates.items():
        edges = sorted(
            (abs(math.log(a["duration_seconds"] / b["duration_seconds"])), a["id"], b["id"])
            for a in outcomes["success"] for b in outcomes["failure"]
        )
        used = set()
        for _, a, b in edges:
            if not used.intersection((a, b)):
                used.update((a, b))
                matched[stratum].append((a, b))

    rng = random.Random(SEED)
    review_cards, pairs = [], []
    for stratum, count in PAIR_COUNTS.items():
        rng.shuffle(matched[stratum])
        if len(matched[stratum]) < count:
            raise ValueError(f"Insufficient matched challenge pairs in {stratum}")
        for pair in matched[stratum][:count]:
            mask = []
            for eid in pair:
                blind = hashlib.sha256(f"{SEED}:{eid}".encode()).hexdigest()[:12]
                mask.append(blind)
                review_cards.append(dict(review_id=blind, episode=eid))
            rng.shuffle(mask)
            pairs.append(dict(review_ids=mask, stratum=stratum))
    rng.shuffle(review_cards)
    payload = dict(
        split_manifest_sha256=digest(splits), review_queue=review_cards, matched_pairs=pairs,
        review_instructions=[
            "Show reviewers only the task and original ordered camera videos. Hide teacher labels, "
            "model identity, pair membership, and the paired trajectory.",
            "Two reviewers independently label episode outcome, failure intervals, categories and cited evidence. "
            "Adjudicate disagreements blind. Report any pairs whose reference outcomes agree.",
            "Freeze the checkpoint and decoding settings using development only before running the final test. "
            "Compare base Qwen, the trained adapter and Astra against the adjudicated labels.",
            "On matched pairs, report both outcomes correct and false alarms on human-verified successes. "
            "Add a task-and-still-frame control to measure how much performance depends on motion evidence.",
            "Report event F1 at temporal IoU thresholds 0.3, 0.5 and 0.7, schema validity, and unsupported "
            "evidence citations by stratum. Compute paired uncertainty by resampling whole recording groups.",
        ],
    )
    contents = (json.dumps(payload, indent=2) + "\n").encode()
    if output.exists() and output.read_bytes() != contents:
        raise ValueError("Refusing to replace the frozen challenge")
    output.write_bytes(contents)
    print(f"Froze {len(pairs)} matched pairs and {len(review_cards)} blind review cards")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("splits", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    freeze_challenge(args.export, args.splits, args.output)
