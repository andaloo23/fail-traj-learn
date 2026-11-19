"""Stage the second recipe using paired nearby failure and clean clips."""
import argparse
from collections import defaultdict
from pathlib import Path
import random

from prepare_astra_pilot import EXCLUDED, SEED, digest, prepare, read


def positive_window(event, n_frames, count):
    center = (event["start_frame"] + event["end_frame"]) // 2
    return min(max(0, center - count // 2), n_frames - count)


def best_clean(negative_segments, center, count):
    starts = [min(max(center - count // 2, x["start_frame"]), x["end_frame"] - count)
              for x in negative_segments if x["end_frame"] - x["start_frame"] >= count]
    return min(starts, key=lambda start: abs(start + count // 2 - center), default=None)


def diverse(groups, count):
    chosen = []
    for index in range(max(map(len, groups.values()), default=0)):
        for group in groups.values():
            if index < len(group):
                chosen.append(group[index])
                if len(chosen) == count:
                    return chosen
    raise ValueError(f"Only {len(chosen)} of {count} eligible windows")


def select_paired(export, splits, first_plan):
    manifest = read(export / "EXPORT_MANIFEST.json")["files"]
    folds = read(splits)["folds"]
    catalog = read(export / "catalog.json")
    rng = random.Random(SEED + 1)
    rng.shuffle(catalog)
    prior_dev = {window["episode"]: window for window in read(first_plan)["windows"]
                 if window["split"] == "development"}
    matched, training_clean = defaultdict(list), defaultdict(list)
    more_dev = {False: defaultdict(list), True: defaultdict(list)}
    shared_dev = []
    for episode in catalog:
        eid = episode["id"]
        fold = folds[eid]
        if eid in EXCLUDED or fold["split"] == "test":
            continue
        ref = f"canonical/{eid}_final/parsed.json"
        expected = manifest[ref]
        if digest(export / ref) != expected:
            raise ValueError(f"Changed canonical label {eid}")
        parsed = read(export / ref)
        split = fold["split"]
        group = fold["group"]
        if eid in prior_dev:
            w = prior_dev[eid]
            assert split == "development"
            shared_dev.append((episode, split, parsed, w["start"], w["count"], expected))
            continue
        positives = [x for x in parsed["segments"] if x["failure"]]
        negatives = [x for x in parsed["segments"] if not x["failure"]]
        count = min(64, episode["n_frames"])
        if split == "development":
            start = (positive_window(min(positives, key=lambda x: x["end_frame"] - x["start_frame"]),
                                     episode["n_frames"], count)
                     if positives else rng.randrange(episode["n_frames"] - count + 1))
            more_dev[bool(positives)][group].append((episode, split, parsed, start, count, expected))
        elif not positives:
            start = rng.randrange(episode["n_frames"] - count + 1)
            training_clean[group].append((episode, split, parsed, start, count, expected))
        else:
            for event in sorted(positives, key=lambda x: x["end_frame"] - x["start_frame"]):
                if event["end_frame"] - event["start_frame"] > 48:
                    break
                pos = positive_window(event, episode["n_frames"], count)
                neg = best_clean(negatives, pos + count // 2, count)
                if neg is not None:
                    matched[group].append(((episode, split, parsed, pos, count, expected),
                                           (episode, split, parsed, neg, count, expected)))
                    break
    training = [row for pair in diverse(matched, 48) for row in pair]
    training.extend(diverse(training_clean, 24))
    rng.shuffle(training)
    shared_dev.sort(key=lambda row: list(prior_dev).index(row[0]["id"]))
    return training + shared_dev + diverse(more_dev[True], 5) + diverse(more_dev[False], 5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("splits", type=Path)
    parser.add_argument("first_plan", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    selected = select_paired(args.export, args.splits, args.first_plan)
    prepare(args.export, args.output.resolve(), "local-pc", args.splits, selected=selected, conservative=True)
