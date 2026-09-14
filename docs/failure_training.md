# Training the failure-attention representation

This implementation is stage 1: supervised failure understanding. It is not yet a calibrated
future-event scorer, RL reward, or causal attribution method. The existing RL training code is
unchanged. Text alignment and prospective scorer training are later stages.

## Architecture

`failure_nets.py` implements a trainable chunk MLP, positional embeddings, a causal transformer,
and three supervised outputs:

- Per-chunk role: progress, failure_inducing, recovery, neutral, aftermath.
- Per-chunk event presence: an observed event onset falls in this chunk (e.g. drop).
- Category-query pooling: one learned query per failure category attends over the available
  window prefix. A separate readout predicts whether that category has appeared in the prefix.

Both transformer self-attention and category pooling mask future positions. Every valid position
gets its own prefix prediction. A separate timing head localizes events; attention is not forced
onto event timestamps. `--pooling last` uses the current contextual representation instead of
category-query attention as an ablation (it still has transformer self-attention).

The input uses the observation at chunk START plus the ordered executed actions and duration of
that chunk. `obs_v2` includes proprioception, cached image features, task-language features, and
normalized episode time. No outcome, cause label, explanation, or event annotation is an input.
This is a retrospective recognition/pretraining objective: the event target can occur after the
pre-chunk observation. Its outputs must NOT be presented as prospective calibrated probabilities.
The loader does not read observations from inside the current chunk. A future prospective model
will require explicit candidate-action semantics and future-horizon targets.

## Data contract

Use an existing `build_dataset.py --obs-spec v2` dataset, and an audited JSON manifest. The
privileged v1 observation is rejected unless `--allow-privileged` explicitly marks a diagnostic.
No annotation file is treated as automatically exhaustive; legacy oracle cause/onset fields
must be reviewed before conversion. A grasp cause is not a drop event.

Minimal structure (illustrative labels only; do not treat this as reviewed real data):

```json
{
  "version": 1,
  "chunk_size": 10,
  "categories": ["grasp", "collision"],
  "event_types": ["drop"],
  "episodes": [
    {
      "dataset": "full_anchor__t0",
      "episode_index": 0,
      "split": "train",
      "split_group": "full_anchor__t0/0",
      "fps": 20,
      "provenance": "reviewer / annotation version",
      "segments": [
        {"start_chunk": 0, "end_chunk_exclusive": 3, "role": "progress"},
        {"start_chunk": 3, "end_chunk_exclusive": 5,
         "role": "failure_inducing", "failure_types": ["grasp"],
         "weight": 0.8, "description": "The object slips during lifting."}
      ],
      "category_coverage": [
        {"start_chunk": 0, "end_chunk_exclusive": 5, "classes": ["grasp"]}
      ],
      "event_coverage": [
        {"start_frame": 0, "end_frame_exclusive": 50, "classes": ["drop"]}
      ],
      "events": [{"type": "drop", "frame": 44, "seconds": 2.2, "weight": 0.9}]
    }
  ]
}
```

Add real validation episodes before training; optional test episodes remain untouched by model
selection. `split_group` must not occur in multiple splits. Use episode keys for episode-held-out
experiments, or policy/setup identifiers for source-held-out experiments. Split before annotation
model selection. The trainer preserves the exact manifest in the run and checkpoint.

Chunk indices are zero-based and boundaries exclusive. This version supports regular recorded
chunks: frames `[j*K, min((j+1)*K, episode_length))`. Verify that this matches the recorder's
actual decision boundaries before preparing the manifest; variable decision boundaries are not
yet supported. Supply the recorded FPS, not a guessed video playback rate. Events use frame
indices within their episode; optional seconds must match within half a frame. End chunks are
padded with an action-valid mask, not silently discarded.

`category_coverage` means all occurrences of the listed failure categories were reviewed in that
interval. Category positives come from segment `failure_types`; covered positions without those
positives are verified negatives. Other categories remain unknown. `event_coverage` separately
means all onsets of the listed physical event types were reviewed. A whole chunk must be covered
to become an event negative; an explicit event supplies a positive even without coverage.
Success, neutral roles, absence of an annotation, and low attention never imply negative labels.
Weights in `(0,1]` are annotation reliability weights, not calibrated probabilities. Omit an
uncertain label instead of supplying weight zero. Role segments must not overlap; multi-class
failure types can share a segment. Descriptions and optional extra metadata are preserved in
provenance but are not model inputs.

For a prefix, any known positive category makes the category target positive. A negative requires
all positions in that prefix to be reviewed. Otherwise it is unknown. Long episodes are divided
into disjoint windows: history and cumulative category targets restart at each window boundary.
All windows stay within one episode; normalization uses unique training chunk-start observations.

## Commands

Use the existing LeRobot environment; no new dependencies or models need downloading:

```bash
PY=/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python
$PY scripts/rl/train_failure_model.py \
  --dataset /home/aliu/projects/fail-traj-learn/rl/datasets/object_v2 \
  --manifest /path/to/reviewed_failure_manifest.json --audit-only

$PY scripts/rl/train_failure_model.py \
  --dataset /home/aliu/projects/fail-traj-learn/rl/datasets/object_v2 \
  --manifest /path/to/reviewed_failure_manifest.json \
  --out /home/aliu/projects/fail-traj-learn/rl/failure_runs/attention_s0 \
  --width 256 --layers 2 --heads 4 --max-chunks 64 --batch-size 32 --epochs 20

$PY -m unittest discover -s scripts/rl -p 'test_failure_model.py' -v
```

The output directory must be new. Default device is CUDA when available; `--device cpu` is
supported. Training uses float32 initially, gradient clipping, and AdamW. Disable an unavailable
supervision task explicitly with `--role-scale 0`, `--event-scale 0`, or `--category-scale 0`.
All active tasks need training and validation supervision. Audit positive AND negative coverage
per class before interpreting discrimination metrics, and match loss scales between ablations.

Outputs: `run.json` (manifest, coverage, arguments), `metrics.jsonl` (validation losses, role
confusion, per-class average precision, Brier score and precision/recall at 0.5), `best.pt` selected
by validation loss, and `last.pt`. Checkpoints include configuration, normalization, vocabularies,
weights, optimizer state, and manifest hash. Brier scores are diagnostics for these recognition
heads, not evidence of calibrated prospective risk. Event metrics currently operate at chunk
resolution; finer timing tolerance metrics and final test evaluation are separate follow-up work.

## Validation boundary

Tests verify no future influence through either attention stage, padded/unknown target masking,
training-only normalization, ordered action packing, frame-to-chunk/second conversion, split
disjointness, gradients through the complete model, synthetic learnability, tied-score metrics,
and a CPU CLI/checkpoint smoke run. These do not establish real rollout quality or policy gains.
