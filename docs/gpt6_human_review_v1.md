# GPT-6 conversation labels with human review

This experiment prepares twelve new LIBERO Object episodes for candidate annotation
by GPT-6 Astra in Codex, followed by candidate-assisted human review. It does not use
the OpenAI API. Each episode uses a fresh three-turn Codex conversation so predictions
cannot leak between episodes. Two conditions are available: the original zero-shot
prompts and a frozen in-context-learning condition with human-labelled demonstrations.

The set is purposively balanced across successful completion, closed loss during
transport, failed release, supported but unsuccessful pickup, wrong-object control,
and held-at-ending behavior. Selection uses private simulator facts only to form the
strata. GPT receives neither those facts nor recorded outcomes. All identities used in
the earlier GPT pilot, audit, sparse/transfer studies, v2 preprocessing study, and v3
holdout are excluded.

## Prepare the frozen pack

Use the LeRobot environment because episode decoding and private selection checks need
PyArrow and the dataset package:

```bash
/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python \
  scripts/annotate/bench/gpt6_human_review_v1.py prepare
```

The command writes ignored artifacts under `outputs/gpt6_human_review_v1/`:

- `episodes/R001` through `R012`: camera arrays for human review, observable telemetry,
  initial image, and chronological pages containing every frame;
- `prompts/<ID>_turn1.md`, `turn2.md`, and `turn3.md`: paste-ready conversation turns;
- `prompts/OUTPUT_SCHEMA.md`: the final candidate contract;
- `input_freeze.json`: hashes of all model-visible inputs;
- `private_manifest.json` and selection provenance: private files the model must not read.

## Run GPT-6 Astra in Codex

For every ID, start a new Codex conversation with GPT-6 Astra. Do not reuse the
conversation for another episode. Send the three corresponding prompt files in order.
For example, tell the clean conversation to follow:

```text
outputs/gpt6_human_review_v1/prompts/R001_turn1.md
```

After it finishes, send turn 2 and then turn 3. Turn 1 writes an evidence ledger,
turn 2 writes a skeptical audit, and turn 3 writes `gpt6_annotation.json`. The prompt
restricts reads procedurally to the episode's public input pack; the filesystem does
not enforce that restriction.

Validate each candidate as it finishes:

```bash
python scripts/annotate/bench/gpt6_human_review_v1.py validate-gpt --id R001
python scripts/annotate/bench/gpt6_human_review_v1.py status
```

After all twelve are complete, freeze them before human review:

```bash
python scripts/annotate/bench/gpt6_human_review_v1.py freeze-gpt
```

## Human review

Open the candidate-assisted annotator:

```bash
/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python \
  scripts/annotate/human_annotator.py \
  outputs/gpt6_human_review_v1/episodes \
  --seed-name gpt6_annotation.json \
  --annotation-name human_review.json
```

Reviewers must verify every segment boundary, description, classification, failure
type, event, and outcome against the camera streams. The editor saves a separate
`human_review.json` and records the source candidate's hash. Because the candidate is
visible, these are assisted corrections rather than independent human labels. If an
independent-human comparison is later desired, use a separate reviewer and output name
without `--seed-name` before showing any model output. A completed assisted review must
explicitly mark the candidate as accepted or corrected; corrections require a reviewer
note.

Freeze the completed reviews with:

```bash
python scripts/annotate/bench/gpt6_human_review_v1.py freeze-human
```

The freeze requires full, contiguous semantic coverage, a resolved success/failure
outcome, specific failure types for failure segments, and the matching GPT candidate
hash.

## Human-demonstration in-context condition

The few-shot condition reuses exactly the same frozen R001--R012 target inputs, but its
first turn shows GPT-6 four completed human-labelled input/output examples before the
unseen target:

- H003: successful pickup and placement;
- H006: missed placement, loss of control, and an unsuccessful recovery attempt;
- H007: collision followed by repeated missed pickups;
- H008: loss of the target followed by wrong-object manipulation.

These four examples were selected for semantic diversity rather than as target-nearest
neighbors. Each is a uniformly sampled full trajectory, with local frame numbers and
human segment boundaries remapped to that local timeline. This keeps the context small
and prevents copying source timestamps. The source annotations were originally made
with the annotator's privileged simulator-contact aid enabled; those hidden signals are
not exported to GPT, but that provenance means this condition should be described as
human-demonstration supervision, not strictly vision-only demonstrations.

Prepare or verify the frozen few-shot pack:

```bash
python scripts/annotate/bench/gpt6_human_review_fewshot_v1.py prepare
```

For each target, start a new GPT-6 Astra Codex conversation and initially send only:

```text
Follow this prompt exactly: outputs/gpt6_human_review_v1/fewshot_v1/prompts/R001_turn1.md
```

When prompted, send `R001_turn2.md` and then `R001_turn3.md` from the same folder.
Repeat in a fresh conversation for every R ID. The outputs use distinct names—
`gpt6_fewshot_observation.json`, `gpt6_fewshot_audit.json`, and
`gpt6_fewshot_annotation.json`—so the zero-shot condition is never overwritten.

Validate a completed candidate, inspect progress, and freeze all candidates with:

```bash
python scripts/annotate/bench/gpt6_human_review_fewshot_v1.py validate-gpt --id R001
python scripts/annotate/bench/gpt6_human_review_fewshot_v1.py status
python scripts/annotate/bench/gpt6_human_review_fewshot_v1.py freeze-gpt
```

After freezing, run candidate-assisted review into a separate human file:

```bash
python scripts/annotate/human_annotator.py \
  outputs/gpt6_human_review_v1/episodes \
  --seed-name gpt6_fewshot_annotation.json \
  --annotation-name human_fewshot_review.json

python scripts/annotate/bench/gpt6_human_review_fewshot_v1.py freeze-human
```

## All-human-demonstration condition (v3)

`fewshot_v3` is a separate, all-twelve-example condition prompted by review of R001.
It retains the frozen v1 result for comparison and shows H001 through H012 before each
target. It contains no hand-written rule derived from the review: the model must infer
approach, divergence, and wrong-object boundary conventions solely from human examples.

Prepare it once:

```bash
/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python \
  scripts/annotate/bench/gpt6_human_review_fewshot_v3.py prepare
```

For R001, start a fresh conversation and use
`outputs/gpt6_human_review_v1/fewshot_v3/prompts/R001_turn1.md`, then turns 2 and 3.
It writes `gpt6_fewshot_v3_observation.json`, `gpt6_fewshot_v3_audit.json`, and
`gpt6_fewshot_v3_annotation.json`. Validate with:

```bash
/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python \
  scripts/annotate/bench/gpt6_human_review_fewshot_v3.py validate-gpt --id R001
```
