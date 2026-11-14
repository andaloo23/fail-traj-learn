"""Check dense reward output; unparseable clips must never become verified negatives."""
import argparse
import json
import math
from pathlib import Path
import re


def rubric_samples_from_manifest(output):
    """Use recorded invocation, so incomplete output cannot define its own sample count."""
    manifest = json.loads((Path(output).parent/'run.json').read_text(encoding='utf-8'))
    command = manifest['command']
    if '--num-samples' in command:
        return int(command[command.index('--num-samples')+1])
    if manifest.get('reference_batch_defaults') is True:
        return 9
    raise ValueError('Cannot establish expected rubric sample count from the run manifest')


def check(path, jobs):
    expected = [json.loads(line)["id"] for line in jobs.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [r["id"] for r in rows]
    issues = []
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        issues.append("Missing, duplicate, or unexpected episode IDs")
    for row in rows:
        if not row.get("clips") or row.get("invalid_clips", 1) != 0 or any(c.get("valid") is not True for c in row.get("clips", [])):
            issues.append(f"{row['id']}: invalid/absent clips; quarantine the episode")
        frames = row.get("frame_scores", [])
        if len(frames) != row.get("num_frames") or any(type(s) is not int or s not in (1, 2, 3) for s in frames):
            issues.append(f"{row['id']}: invalid or missing frame scores")
    return dict(episodes=len(rows), structurally_valid=not issues, issues=issues,
                human_verified=False, label_names={"1": "failure", "2": "suboptimal", "3": "normal"},
                training_ready=False,
                note="Human review and an explicit schema adapter are required before training.")


def check_rubric(path, jobs, expected_samples=1):
    """Require retained reasoning and genuine allowed scores, before upstream clamping."""
    source = [json.loads(s) for s in jobs.read_text(encoding="utf-8").splitlines() if s.strip()]
    rows = [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]
    expected = {r["id"]: r for r in source}
    ids = [r["id"] for r in rows]
    issues, lengths = [], {}
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        issues.append("Missing, duplicate, or unexpected episode IDs")
    for row in rows:
        job = expected.get(row["id"])
        if job is None:
            continue
        prefix = row["id"] + ": "
        if row.get("task") != job["task"] or row.get("steps") != [s["action"] for s in job["rubric"]]:
            issues.append(prefix + "task or rubric differs")
        samples = row.get("samples", [])
        if len(samples) != expected_samples or row.get("parsed_samples") != len(samples):
            issues.append(prefix + "incomplete or unparsed samples")
        for sample in samples:
            reasoning = sample.get("thinking")
            if sample.get("parsed") is not True or not isinstance(reasoning, str) or not reasoning.strip():
                issues.append(prefix + "missing reasoning or incomplete final answer")
            match = re.fullmatch(r"\s*ANSWER:\s*(\[[^\]]*\])\s*", sample.get("answer", ""))
            try:
                scores = json.loads(match.group(1)) if match else None
            except ValueError:
                scores = None
            valid = isinstance(scores, list) and len(scores) == len(job["rubric"])
            if valid:
                for score, step in zip(scores, job["rubric"]):
                    if (type(score) not in (int, float) or not math.isfinite(score)
                            or not any(abs(score - g["points"]) < 1e-6 for g in step["grading"])):
                        valid = False
            if not valid or scores != sample.get("scores"):
                issues.append(prefix + "raw answer has missing, clamped, or disallowed scores")
        index = row.get("medoid_sample")
        if type(index) is not int or not 0 <= index < len(samples):
            issues.append(prefix + "missing selected sample")
        else:
            selected = samples[index]
            scores = selected.get("scores")
            if row.get("scores") != scores or not isinstance(scores, list) or row.get("total") != round(sum(scores), 4):
                issues.append(prefix + "selected scores or total differ")
            lengths[row["id"]] = len((selected.get("thinking") or "").split())
    return dict(episodes=len(rows), structurally_valid=not issues, issues=issues,
                reasoning_words=lengths, human_verified=False, training_ready=False,
                note="Generic-rubric pilot; retained reasoning and scores still need human video review.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--jobs", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    result = check(a.output, a.jobs)
    a.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["structurally_valid"] else 1)
