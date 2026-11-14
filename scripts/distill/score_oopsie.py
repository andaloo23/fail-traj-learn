"""Offline teacher agreement or explicitly sourced human-reference evaluation."""
import argparse
import json
from pathlib import Path

import oopsie_common as common
import oopsie_markdown
from trajectory_metrics import evaluate
from oopsie_pipeline import validate


def segments(value, offset=0):
    return [dict(s, start=s["start_frame"]-offset, end=s["end_frame"]-offset) for s in value["segments"]]


def reference_index(folder):
    path = Path(folder) / "references.md"
    if not path.exists():
        return common.read(Path(folder) / "references.json")
    header, separator, entries = path.read_text(encoding="utf-8").partition("\n## Episodes\n")
    if not separator or not header.startswith("# Independent human references\n"):
        raise ValueError("Independent Markdown references need a title and Episodes section")
    fields = oopsie_markdown.bullet_values(header.partition("\n")[2])
    if set(fields) != {"Kind", "Reviewers", "Blind to teacher", "Manifest SHA-256"}:
        raise ValueError("Independent reference provenance fields are incomplete")
    episodes = {}
    for eid, value in oopsie_markdown.bullet_values(entries).items():
        name, separator, digest = value.partition("|")
        if not separator:
            raise ValueError("Reference episode entries need an annotation filename and its SHA-256")
        episodes[eid] = dict(annotation=name.strip(), sha256=digest.strip())
    return dict(kind=fields["Kind"], reviewers=[s.strip() for s in fields["Reviewers"].split(";") if s.strip()],
                blind_to_teacher=fields["Blind to teacher"] == "Yes", manifest_sha256=fields["Manifest SHA-256"], episodes=episodes)


def score(run, predictions=None, references=None, split="development"):
    manifest = common.verify(run)
    human = reference_index(references) if references else None
    if references and not predictions:
        raise ValueError("Human references require a student predictions directory")
    if human:
        if human["kind"] != "independent_human" or not human["reviewers"] or not human["blind_to_teacher"]:
            raise ValueError("Independent references need named reviewers and a blind annotation protocol")
        if human["manifest_sha256"] != common.sha(Path(run) / "manifest.json"):
            raise ValueError("Human references use a different evidence/split manifest")
    if predictions:
        receipt = common.read(Path(predictions) / "generation.json")
        if receipt["manifest_sha256"] != common.sha(Path(run) / "manifest.json") or receipt["split"] != split:
            raise ValueError("Predictions use a different frozen run or split")
    if not human and validate(run)["invalid"]:
        raise ValueError("Invalid teacher traces; inspect validation before scoring")
    rows = []
    for episode in manifest["episodes"]:
        if episode["split"] != split:
            continue
        eid = episode["id"]
        if human:
            source = human["episodes"][eid]
            path = common.inside(references, source["annotation"])
            if common.sha(path) != source["sha256"]:
                raise ValueError("Human reference hash changed")
            ref = common.parse_answer(path.read_bytes().decode("utf-8"), "markdown" if path.suffix == ".md" else "json")
        else:
            ref = common.load_annotation(Path(run) / f"traces/{eid}_sol", manifest)
        common.validate_annotation(ref, episode)
        valid, error, truncated = True, None, False
        if predictions:
            try:
                saved = common.read(Path(predictions) / (eid + ".json"))
                truncated = saved["hit_max"]
                pred = common.parse_answer(saved["text"], common.annotation_format(manifest))
                common.validate_annotation(pred, episode)
                pred_segments = segments(pred, episode.get("window_start_frame", 0))
            except (OSError, KeyError, ValueError, TypeError) as exc:
                valid, error, pred_segments = False, str(exc), []
        else:
            pred = common.load_annotation(Path(run) / f"traces/{eid}_astra", manifest)
            common.validate_annotation(pred, episode)
            pred_segments = segments(pred, episode.get("window_start_frame", 0))
        start, end = episode.get("window_start_frame", 0), episode.get("window_end_frame", episode["n_frames"])
        metrics = evaluate(pred_segments, segments(ref, start), end-start, episode["fps"],
                           require_verified=bool(human), label_mode="failure_binary")
        rows.append(dict(episode=eid, schema_valid=valid, error=error, hit_max=truncated, metrics=metrics))
    if not rows:
        raise ValueError("No episodes in selected split")
    totals = {key: sum(row["metrics"]["axes"]["failure"][key] for row in rows) for key in ("tp", "fp", "fn", "tn")}
    tp, fp, fn = (totals[key] for key in ("tp", "fp", "fn"))
    totals.update(precision=tp / (tp + fp) if tp + fp else None,
                  recall=tp / (tp + fn) if tp + fn else None,
                  f1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None)
    categories = {}
    names = sorted({name for row in rows for name in row["metrics"]["failure_types"]})
    for name in names:
        counts = {key: sum(row["metrics"]["failure_types"].get(name, {}).get(key, 0) for row in rows)
                  for key in ("tp", "fp", "fn")}
        denominator = 2 * counts["tp"] + counts["fp"] + counts["fn"]
        if denominator:
            categories[name] = dict(counts, f1=2 * counts["tp"] / denominator)
    return dict(kind="independent_human_reference" if human else "teacher_agreement",
                scope="Pilot only; two held-out episodes do not establish generalization.",
                reference="human" if human else "sol", prediction="student" if predictions else "astra",
                split=split, n=len(rows), schema_valid_rate=sum(r["schema_valid"] for r in rows) / len(rows),
                failure_micro=totals, episodes=rows,
                category_micro_counts=categories,
                category_macro_f1=sum(c["f1"] for c in categories.values()) / len(categories) if categories else None,
                limitations="Teacher agreement does not establish correctness. Uncertain teacher references remain provisional. "
                            "Scores retain conservative whole-segment review exclusions, including v3 partial targets; "
                            "overlapping windows are correlated and are not independent episodes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--references", type=Path)
    parser.add_argument("--split", choices=("train", "development", "test"), default="development")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = score(args.run, args.predictions, args.references, args.split)
    common.write(args.out, result)
    print(json.dumps({k: v for k, v in result.items() if k != "episodes"}, indent=2))
