#!/usr/bin/env python3
"""Prepare and freeze the human-demonstration GPT-6 annotation condition.

This condition reuses the frozen R001--R012 target inputs from
``gpt6_human_review_v1``.  Each fresh conversation first sees the same four
temporally sampled, human-labelled H demonstrations, then labels one R target.

Commands:
  prepare        export demonstrations and write/freeze few-shot prompts
  status         report few-shot GPT and human-review progress
  validate-gpt   validate one or all few-shot conversation outputs
  freeze-gpt     freeze all twelve few-shot candidates
  freeze-human   validate and freeze all twelve assisted human reviews
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import gpt6_human_review_v1 as base

BASE_OUT = ROOT / "outputs" / "gpt6_human_review_v1"
OUT = BASE_OUT / "fewshot_v1"
SOURCE = ROOT / "outputs" / "preprocessing_ablation_v3" / "holdout_source"
EXAMPLE_IDS = ("H003", "H006", "H007", "H008")
STRIDE = 4
VERSION = "gpt6_human_review_fewshot_v1"
MODEL = base.MODEL

OBSERVATION_NAME = "gpt6_fewshot_observation.json"
AUDIT_NAME = "gpt6_fewshot_audit.json"
CANDIDATE_NAME = "gpt6_fewshot_annotation.json"
REVIEW_NAME = "human_fewshot_review.json"


def sampled_indices(n_frames: int, stride: int = STRIDE) -> list[int]:
    if n_frames < 1:
        raise ValueError("demonstration must contain at least one frame")
    values = list(range(0, n_frames, stride))
    if values[-1] != n_frames - 1:
        values.append(n_frames - 1)
    return values


def remap_segments(segments: list[dict], indices: list[int]) -> list[dict]:
    """Map source half-open segments onto temporally sampled local frames."""
    result = []
    expected = 0
    for segment in segments:
        local = [i for i, source_frame in enumerate(indices)
                 if int(segment["start"]) <= source_frame < int(segment["end"])]
        if not local:
            raise ValueError(f"sampling dropped source segment {segment}")
        if local[0] != expected or local != list(range(local[0], local[-1] + 1)):
            raise ValueError("sampled demonstration segments are not contiguous")
        classification = str(segment["classification"])
        result.append({
            "start": local[0],
            "end": local[-1] + 1,
            "text": str(segment["text"]),
            "classification": classification,
            "failure_type": (str(segment.get("failure_type") or "unknown")
                             if classification == "failure" else "unknown"),
            "note": str(segment.get("note") or ""),
        })
        expected = local[-1] + 1
    if expected != len(indices):
        raise ValueError("sampled demonstration labels do not cover every local frame")
    return result


def example_files() -> list[Path]:
    files = [OUT / "example_manifest.json"]
    for ident in EXAMPLE_IDS:
        folder = OUT / "examples" / ident
        files.extend([folder / "manifest.json", folder / "observable.json",
                      folder / "initial.jpg", folder / "human_label.json"])
        files.extend(sorted((folder / "pages").glob("*.jpg")))
    return files


def prompt_files() -> list[Path]:
    return sorted(path for path in (OUT / "prompts").iterdir() if path.is_file())


def expected_input_files() -> list[Path]:
    return example_files() + prompt_files()


def verify_freeze() -> None:
    base.verify_input_freeze()
    frozen = base.read(OUT / "fewshot_input_freeze.json")
    if frozen.get("base_input_freeze_sha256") != base.sha(BASE_OUT / "input_freeze.json"):
        raise RuntimeError("the reused target input freeze changed")
    current = {str(path.relative_to(OUT)): base.sha(path) for path in expected_input_files()}
    if frozen.get("sha256") != current:
        missing = sorted(set(frozen.get("sha256", {})) - set(current))
        added = sorted(set(current) - set(frozen.get("sha256", {})))
        changed = sorted(key for key in set(current) & set(frozen.get("sha256", {}))
                         if current[key] != frozen["sha256"][key])
        raise RuntimeError(f"few-shot freeze mismatch: missing={missing}, added={added}, changed={changed}")


def export_examples() -> None:
    manifest = []
    provenance = []
    for ident in EXAMPLE_IDS:
        source = SOURCE / ident
        label_path = source / "human_annotation.json"
        if not source.is_dir() or not label_path.is_file():
            raise FileNotFoundError(source)
        label = base.read(label_path)
        observable = base.read(source / "observable.json")
        with np.load(source / "cameras.npz") as arrays:
            agent = np.asarray(arrays["agent"])
            wrist = np.asarray(arrays["wrist"])
        if agent.shape != wrist.shape or len(agent) != len(observable["telemetry"]):
            raise ValueError(f"invalid demonstration streams for {ident}")
        indices = sampled_indices(len(agent))
        local_telemetry = []
        for local_frame, source_frame in enumerate(indices):
            row = dict(observable["telemetry"][source_frame])
            row["frame"] = local_frame
            local_telemetry.append(row)
        folder = OUT / "examples" / ident
        folder.mkdir(parents=True, exist_ok=True)
        local_agent, local_wrist = agent[indices], wrist[indices]
        base.render_initial(local_agent, local_wrist, folder / "initial.jpg", ident)
        pages = base.render_pages(local_agent, local_wrist, local_telemetry, folder, ident)
        example_observable = {
            "id": ident,
            "task": label["task"],
            "n_frames": len(indices),
            "fps": observable.get("fps", base.FPS) / STRIDE,
            "frame_bounds": "local zero-based, end-exclusive",
            "notes": (
                "This is a uniformly sampled full trajectory. Frame numbers are local to this "
                "demonstration. Finger positions and commands are not proof of contact."
            ),
            "telemetry": local_telemetry,
        }
        human_label = {
            "version": "human_demonstration_v1",
            "id": ident,
            "task": label["task"],
            "n_frames": len(indices),
            "fps": observable.get("fps", base.FPS) / STRIDE,
            "episode_outcome": label["episode_outcome"],
            "segments": remap_segments(label["segments"], indices),
            "events": [],
            "trajectory_note": str(label.get("trajectory_note") or ""),
        }
        base.save(folder / "observable.json", example_observable)
        base.save(folder / "human_label.json", human_label)
        base.save(folder / "manifest.json", {
            "version": "human_demonstration_v1",
            "id": ident,
            "task": label["task"],
            "n_frames": len(indices),
            "fps": example_observable["fps"],
            "initial_image": "initial.jpg",
            "pages": pages,
            "supplied_frames": list(range(len(indices))),
            "notes": (
                "Complete trajectory sampled at one frame per four source frames plus the final "
                "frame. All displayed frame numbers are local to this example."
            ),
        })
        relative = f"examples/{ident}"
        manifest.append({
            "id": ident,
            "purpose": "human-labelled input/output demonstration",
            "manifest": f"{relative}/manifest.json",
            "observable": f"{relative}/observable.json",
            "initial_image": f"{relative}/initial.jpg",
            "human_label": f"{relative}/human_label.json",
            "pages": [f"{relative}/{page}" for page in pages],
        })
        provenance.append({
            "id": ident,
            "source_human_annotation": str(label_path.relative_to(ROOT)),
            "source_human_annotation_sha256": base.sha(label_path),
            "source_annotation_aids": label.get("annotation_aids", []),
            "source_frames": len(agent),
            "local_frames": len(indices),
            "stride": STRIDE,
        })
        print(ident, len(indices), "sampled frames", len(pages), "pages", flush=True)
    base.save(OUT / "example_manifest.json", {
        "version": "human_demonstration_v1",
        "examples": manifest,
        "instruction": (
            "For each example, inspect all listed pages as its input, then read human_label.json "
            "as the demonstrated output. Example frame numbers are local and unrelated to targets."
        ),
    })
    base.save(OUT / "example_provenance_private.json", {
        "version": VERSION,
        "not_model_visible": True,
        "examples": provenance,
    })


SCHEMA = base.SCHEMA.replace('"gpt6_human_review_v1"', f'"{VERSION}"')


def prompt_one(ident: str) -> str:
    target = f"outputs/gpt6_human_review_v1/episodes/{ident}"
    root = f"outputs/gpt6_human_review_v1/{OUT.name}"
    examples = "\n".join(
        f"- `{root}/examples/{example}/manifest.json`, `observable.json`, every listed page, "
        f"and then `human_label.json`" for example in EXAMPLE_IDS
    )
    return f"""# Turn 1 of 3: few-shot evidence pass for {ident}

This is a blinded robot-trajectory annotation run. Complete this evidence pass now;
do not ask questions, delegate, browse the web, or inspect unrelated repository files.

You may read only the following human-labelled demonstrations:
{examples}

and these target inputs:
- `{target}/manifest.json`
- `{target}/observable.json`
- `{target}/initial.jpg`
- every target image listed by the target manifest
- this prompt file

First study every demonstration as an input/output pair: inspect every page listed in
its manifest, then read its `human_label.json`. The examples demonstrate task-level
segment classification, failure-type distinctions, outcome judgment, and boundary
granularity. Their displayed frame numbers are local to each downsampled example and
have no numerical relationship to {ident}. Do not copy their objects, prose, outcomes,
or frame boundaries into the target. The demonstrations contain no event labels, so
they are not evidence that the target has no physical events.

Then inspect every page listed in `{target}/manifest.json` at full available detail.
The target outcome is withheld. Identify the instructed target independently from the
object the robot happens to manipulate. Build an evidence ledger with target identity,
observable interaction phases, possible grasp/contact/loss/release/settling transitions,
useful progress, harmful actions, attempted recovery, and uncertainty. Check images
against telemetry without treating commands or finger positions as contact truth.

Write `{target}/{OBSERVATION_NAME}` with keys `id`, `studied_examples`,
`inspected_pages`, `target_description`, `phase_ledger`, `transition_candidates`, and
`uncertainties`. `studied_examples` must equal `{json.dumps(list(EXAMPLE_IDS))}` and
`inspected_pages` must exactly equal the target manifest page list. Cite target frame
numbers in every phase and transition. Do not write final segments or the candidate in
this turn. Respond only with a short completion message asking for turn 2.
"""


def prompt_two(ident: str) -> str:
    target = f"outputs/gpt6_human_review_v1/episodes/{ident}"
    return f"""# Turn 2 of 3: few-shot skeptical audit for {ident}

Continue the same conversation. Re-read `{target}/{OBSERVATION_NAME}` plus the target
manifest and observable telemetry. Reinspect relevant supplied target pages. The read
restrictions from turn 1 remain in force; the four human demonstrations may be
revisited, but do not inspect any other episodes, hidden references, prior predictions,
private manifests, evaluation results, or other human labels.

Audit the target ledger rather than endorsing it. Examine the trajectory forwards and
backwards around every gripper-command change and proposed transition. Test for brief
supported pinches, squeeze-out, residual one-sided contact, closed-command loss,
opening-associated release, wrong-object interaction, regrasp, and settling. Separate
physical facts from task-level judgments. Remove transitions supported only by command
or finger position, and retain `unknown` when occlusion prevents a decision. Apply the
demonstrated semantics, not the demonstrations' episode-specific conclusions.

Write `{target}/{AUDIT_NAME}` with keys `id`, `checked_command_runs`,
`supported_transitions`, `rejected_transitions`, `possible_omissions`,
`semantic_questions`, and `remaining_uncertainties`. Cite target frames and visible
evidence. Do not write the final annotation yet. Respond only with a short completion
message asking for turn 3.
"""


def prompt_three(ident: str) -> str:
    target = f"outputs/gpt6_human_review_v1/episodes/{ident}"
    schema = f"outputs/gpt6_human_review_v1/{OUT.name}/prompts/OUTPUT_SCHEMA.md"
    examples = ", ".join(EXAMPLE_IDS)
    return f"""# Turn 3 of 3: few-shot final candidate for {ident}

Continue the same conversation. Reconcile `{target}/{OBSERVATION_NAME}` and
`{target}/{AUDIT_NAME}` against target images and telemetry. Follow `{schema}` exactly.

Produce a concise full-episode segmentation using the distinctions demonstrated by
{examples}. Classify intervals by task-level effect: `progress`
advances the instructed task; `failure` introduces or worsens an observable error;
`recovery` attempts to restore progress after an error; `neutral` has no clear task
effect. An attempted correction can remain failure when it repeats or worsens the
error. Infer success only when the visible result supports it. Do not invent hidden
physical events or transfer example-specific labels to this target.

Write the final object to `{target}/{CANDIDATE_NAME}`. Validate its ID, exact half-open
coverage from 0 through `n_frames`, enums, event bounds, and evidence frames. Do not
alter prior artifacts. Respond with the output path and a one-sentence validation
result.
"""


def write_prompts() -> None:
    folder = OUT / "prompts"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "OUTPUT_SCHEMA.md").write_text(SCHEMA, encoding="utf-8")
    (folder / "README.md").write_text(
        "# Human-demonstration GPT-6 prompts\n\n"
        "Start a fresh GPT-6 Astra Codex conversation for each R episode and send its "
        "three prompt files in order. Turn 1 supplies the same four frozen human-labelled "
        "demonstrations before the unseen target. Never reuse a conversation across IDs.\n",
        encoding="utf-8",
    )
    for ident in base.IDS:
        for number, content in ((1, prompt_one(ident)), (2, prompt_two(ident)),
                                (3, prompt_three(ident))):
            (folder / f"{ident}_turn{number}.md").write_text(content, encoding="utf-8")


def prepare() -> None:
    if not (BASE_OUT / "input_freeze.json").exists():
        raise FileNotFoundError("prepare gpt6_human_review_v1 before the few-shot condition")
    if (OUT / "fewshot_input_freeze.json").exists():
        verify_freeze()
        print("Existing frozen few-shot pack verified; no inputs rewritten", flush=True)
        return
    export_examples()
    write_prompts()
    hashes = {str(path.relative_to(OUT)): base.sha(path) for path in expected_input_files()}
    base.save(OUT / "fewshot_input_freeze.json", {
        "version": VERSION,
        "model": MODEL,
        "conversation_policy": "fresh three-turn Codex conversation per target",
        "base_input_freeze_sha256": base.sha(BASE_OUT / "input_freeze.json"),
        "example_ids": list(EXAMPLE_IDS),
        "sha256": hashes,
    })
    (OUT / "README.md").write_text(
        "# GPT-6 human-demonstration condition\n\n"
        "The fixed demonstrations are H003, H006, H007, and H008. Start one fresh "
        "conversation per R target and send `prompts/<ID>_turn1.md`, then turns 2 and 3. "
        f"The model writes `{OBSERVATION_NAME}`, `{AUDIT_NAME}`, and `{CANDIDATE_NAME}` "
        "inside the reused target episode folder.\n",
        encoding="utf-8",
    )
    print("Prepared and froze", len(EXAMPLE_IDS), "human demonstrations", flush=True)


def validate_observation(observation: dict, audit: dict, manifest: dict) -> None:
    if observation.get("studied_examples") != list(EXAMPLE_IDS):
        raise ValueError("observation studied_examples must list the fixed demonstrations")
    base.validate_conversation_artifacts(observation, audit, manifest)


def validate_candidate(value: dict, meta: dict) -> dict:
    if value.get("version") != VERSION:
        raise ValueError(f"candidate version must be {VERSION!r}")
    compatible = dict(value)
    compatible["version"] = "gpt6_human_review_v1"
    base.validate_gpt_annotation(compatible, meta)
    return value


def validate_gpt(requested: str | None = None) -> list[Path]:
    verify_freeze()
    paths = []
    for ident in base.selected_ids(requested):
        episode = BASE_OUT / "episodes" / ident
        observation_path = episode / OBSERVATION_NAME
        audit_path = episode / AUDIT_NAME
        candidate_path = episode / CANDIDATE_NAME
        for path in (observation_path, audit_path, candidate_path):
            if not path.exists():
                raise FileNotFoundError(path)
        validate_observation(base.read(observation_path), base.read(audit_path),
                             base.read(episode / "manifest.json"))
        validate_candidate(base.read(candidate_path), base.read(episode / "observable.json"))
        paths.extend((observation_path, audit_path, candidate_path))
        print(ident, "few-shot conversation artifacts valid", flush=True)
    return paths


def freeze_gpt() -> None:
    paths = validate_gpt()
    freeze = OUT / "gpt_freeze.json"
    value = {
        "version": VERSION,
        "fewshot_input_freeze_sha256": base.sha(OUT / "fewshot_input_freeze.json"),
        "conversation_artifact_sha256": {
            str(path.relative_to(BASE_OUT)): base.sha(path) for path in paths
        },
    }
    if freeze.exists() and base.read(freeze) != value:
        raise RuntimeError("few-shot GPT freeze does not match current candidates")
    base.save(freeze, value)
    print("Frozen", len(paths) // 3, "few-shot GPT conversations", flush=True)


def freeze_human() -> None:
    if not (OUT / "gpt_freeze.json").exists():
        raise RuntimeError("freeze few-shot GPT candidates before human review")
    freeze_gpt()
    paths = []
    for ident in base.IDS:
        episode = BASE_OUT / "episodes" / ident
        review_path = episode / REVIEW_NAME
        candidate_path = episode / CANDIDATE_NAME
        if not review_path.exists():
            raise FileNotFoundError(review_path)
        base.validate_human_review(base.read(review_path),
                                   base.read(episode / "observable.json"), candidate_path)
        paths.append(review_path)
        print(ident, "few-shot human review valid", flush=True)
    freeze = OUT / "human_freeze.json"
    value = {
        "version": VERSION,
        "gpt_freeze_sha256": base.sha(OUT / "gpt_freeze.json"),
        "human_review_sha256": {
            str(path.relative_to(BASE_OUT)): base.sha(path) for path in paths
        },
    }
    if freeze.exists() and base.read(freeze) != value:
        raise RuntimeError("few-shot human freeze does not match current reviews")
    base.save(freeze, value)
    print("Frozen", len(paths), "few-shot human reviews", flush=True)


def status() -> None:
    rows = []
    for ident in base.IDS:
        episode = BASE_OUT / "episodes" / ident
        rows.append({
            "id": ident,
            "observation": (episode / OBSERVATION_NAME).exists(),
            "audit": (episode / AUDIT_NAME).exists(),
            "candidate": (episode / CANDIDATE_NAME).exists(),
            "human_review": (episode / REVIEW_NAME).exists(),
        })
    print(json.dumps({
        "fewshot_input_frozen": (OUT / "fewshot_input_freeze.json").exists(),
        "gpt_frozen": (OUT / "gpt_freeze.json").exists(),
        "human_frozen": (OUT / "human_freeze.json").exists(),
        "examples": list(EXAMPLE_IDS),
        "episodes": rows,
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=[
        "prepare", "status", "validate-gpt", "freeze-gpt", "freeze-human",
    ])
    parser.add_argument("--id", help="single R episode ID for validate-gpt")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "status":
        status()
    elif args.command == "validate-gpt":
        validate_gpt(args.id)
    elif args.command == "freeze-gpt":
        freeze_gpt()
    elif args.command == "freeze-human":
        freeze_human()


if __name__ == "__main__":
    main()
