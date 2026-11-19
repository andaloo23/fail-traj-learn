"""Score downloaded blind-development outputs with strict event and frame metrics."""
import argparse
import json
from pathlib import Path
import re

from qwen_astra_pilot import failure_intervals, read
from score_flora_style import max_matching, tiou

THRESHOLDS = (0.3, 0.5, 0.7)


def score_example(window, text):
    start, stop = window["start"], window["start"] + window["count"]
    gold = failure_intervals(window["targets"]["SCE"], start, stop)
    gold_frames = {frame for a, b in gold for frame in range(a, b)}
    try:
        predicted = failure_intervals(text, start, stop)
        valid = True
    except ValueError:
        predicted = []
        valid = False
    predicted_frames = {frame for a, b in predicted for frame in range(a, b)}
    event_f1 = {}
    for threshold in THRESHOLDS:
        adj = [[j for j, actual in enumerate(gold) if tiou(prediction, actual) >= threshold]
               for prediction in predicted]
        total = len(predicted) + len(gold)
        event_f1[str(threshold)] = (2 * max_matching(adj, len(gold)) / total if total else 1.0) if valid else 0.0

    details = text.partition("# Visible failure details")[2]
    evidence_rows = re.findall(r"(?m)^\|\s*(\d+)\s*\|\s*(\d+)\s*\|([^\n|]*)\|([^\n|]*)\|", details)
    cited = []
    for a, b, categories, explanation in evidence_rows:
        refs = [int(n) for n in re.findall(r"\bframes?\s+(\d+)", explanation, re.I)]
        cited.append(dict(start=int(a), stop=int(b), categories=categories.strip(), frame_refs=refs,
                          outside_visible_interval=any(not start <= n < stop for n in refs)))
    return dict(id=window["id"], valid=valid, gold_event_count=len(gold), event_f1=event_f1,
                tp=len(predicted_frames & gold_frames), fp=len(predicted_frames - gold_frames),
                fn=len(gold_frames - predicted_frames),
                false_alarm=valid and not gold and bool(predicted), evidence=cited)


def score(plan, folder):
    development = [w for w in plan["windows"] if w["split"] == "development"]
    result = {}
    for arm in ("base", "adapter", "always_failure", "never_failure"):
        records = []
        for window in development:
            if arm in ("always_failure", "never_failure"):
                start, stop = window["start"], window["start"] + window["count"]
                status = "Yes" if arm == "always_failure" else "No"
                text = f"# Failure segments\n| {start} | {stop} | {status} |"
            else:
                prediction = folder / f"{window['id']}_{arm}.md"
                text = prediction.read_text(encoding="utf-8") if prediction.is_file() else ""
            records.append(score_example(window, text))
        tp, fp, fn = (sum(row[key] for row in records) for key in ("tp", "fp", "fn"))
        result[arm] = dict(windows=len(records), valid=sum(r["valid"] for r in records),
                           event_f1={str(t): sum(row["event_f1"][str(t)] for row in records) / len(records)
                                     for t in THRESHOLDS},
                           frame_failure_f1=2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None,
                           false_alarms_in_clean_clips=sum(row["false_alarm"] for row in records),
                           clean_clips=sum(not row["gold_event_count"] for row in records),
                           per_window=records)
    return result


def worthy_of_review(metrics):
    """Require complete outputs, no added clean-clip alarms, and a localization gain."""
    base, adapter = metrics["base"], metrics["adapter"]
    if base["valid"] != base["windows"] or adapter["valid"] != adapter["windows"]:
        return False
    if adapter["false_alarms_in_clean_clips"] > base["false_alarms_in_clean_clips"]:
        return False
    baseline = (base["event_f1"]["0.5"], base["frame_failure_f1"])
    candidate = (adapter["event_f1"]["0.5"], adapter["frame_failure_f1"])
    return (all(left is not None and right is not None and left >= right
                for left, right in zip(candidate, baseline)) and candidate != baseline)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    print(json.dumps(score(read(args.plan), args.predictions), indent=2))
