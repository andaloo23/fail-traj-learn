# VLM segmentation pipeline (scripts/annotate/)

Implements proposal section 4: a zero-shot vision-language model labels every action chunk of an episode with
`progress | failure_inducing | recovery | neutral | aftermath`, estimates the landmarks `failure_onset`,
`decisive_error` (t*), `visible_failure`, `recoverable_until`, and names an OOPSIE-aligned cause. Confidence `q_t`
comes from self-consistency over K sampled diagnoses, not from the model's own confidence field.

## Current revision: p8 / annot_v2

The separate [observable-event experiment](event_experiment.md) tests local visual recognition and an
overlapping-window episode scan before further segmentation changes. It leaves production annotations intact.

The p2-p7 notes below describe historical experiments. p8 supersedes their rendering, identification,
validation, voting and refinement behavior:

- Every chunk has explicitly captioned start/end observations. Image groups contain all their chunks;
  no grouped chunk is silently omitted. Paired-camera cells are downsampled to bound token cost. The
  signal table describes end-of-chunk observations, not necessarily the pictured start state. This trades
  spatial resolution for temporal coverage; dense refinement and wrist identification retain larger images.
- At most four candidate holding chunks receive separate wrist identification calls. Each hypothesis is
  scoped to that exact midpoint observation, matches an unambiguous object name, and remains tentative.
  No holding candidates means no claim about whether anything was held. Finger position is not contact evidence.
- Parsing rejects gaps, overlaps, reversed/out-of-range/fractional indices, unknown labels and invalid
  confidences. Aliases are still normalized. Full raw responses are retained, including successful samples.
- All valid samples vote, including single-label episodes. `q` is explicitly uncalibrated vote support over
  every attempted diagnosis (including invalid attempts and retries). Without a strict majority, q=0;
  the displayed plurality label is diagnostic only. Single-label flags do not prove an annotation is wrong.
- Skipped successes retain placeholder progress labels with q=0. Their outcome is still usable, but these
  placeholders must not become verified per-chunk advantage constraints. Use `--include-clean` to annotate them.
- `--refine` checks every predicted decisive error, including unanimous predictions. Refined indices must
  lie inside the shown window. Null/invalid refinement responses cannot erase supported coarse landmarks.
- The annotation loader and routing apply `scripts/analysis/exclusions.json` outcome corrections. Records
  preserve `recorded_success` as well as effective `success`. Label export rejects stale outcome records and
  missing episode offsets rather than assigning rows to episode zero. Raw datasets/rewards are unchanged;
  downstream training must use the same corrections when constructing rewards.
- Evaluation reports absent records, failed annotations, length mismatches and missing decisive errors.
  False alarms are measured only on VLM-evaluated reference-clean successes, not recovered successes or
  automatically labeled defaults. Timing accuracy is additionally reported with missing predictions counted
  as misses across all reference episodes, including absent/invalid predictions.

Use a new tag for p8. Resuming a tag containing older schemas/prompts fails explicitly; existing records are
never silently upgraded. No old annotations have been overwritten by this revision.

```
annotate.sh --datasets full_shift8 --refine --tag qwen3vl8b_p8
py.sh to_labels.py qwen3vl8b_p8
# CPU regression checks from the repository root, using the LeRobot Python:
python -m unittest discover -s scripts/annotate -p 'test_*.py'
```

The exporter includes `needs_review` and `training_q`. Downstream annotation losses must use `training_q`,
not raw `q`: a decisive error outside a failure-inducing segment or absence of majority supervision masks the
episode. Raw votes remain available for review. Refinement cannot replace a coarse non-decisive landmark that
lies outside its visible window.

Validation: eight CPU regression tests, real corrected-outcome render for full_shift16__t3 episode 28,
and a three-sample GPU smoke run plus parquet export for full_shift8__t0 episode 0. The smoke run used
about 19.85 GiB and 60 seconds. It still produced an incorrect early decisive-error hypothesis (chunk 3 after
refinement, versus the earlier review's slip near chunk 12), despite unanimous segment votes. The exported
smoke episode is masked by the cross-field review check. Do not treat this smoke tag as validated training data
or claim semantic improvement from these implementation checks.

These are implementation safeguards, not evidence that p8 semantic labels are accurate. A reviewed reference
set is still required before using vote support as confidence or accepting temporal labels as advantage signs.

## Design decisions (2026-09-07)

* **Unit = the recorder's 10-step action chunk** (0.5 s at 20 fps; `chunk.index` column). Segment boundaries and t*
  are chunk indices, which is also the actor's action horizon.
* **What the model sees**: one 512x256 tile per chunk (agentview | wrist, middle frame of the chunk) with the chunk
  index burned in and repeated as text before the image; the task instruction; the outcome; a per-chunk table of
  non-privileged signals (end-effector xyz from `observation.state[:3]`, aperture from `observation.state[6]`,
  gripper command from `action[6]`, speed, dz); a glossary of what the named scene objects look like.
  **No `priv.*` column is ever shown to the model** (they are the oracle). Episodes longer than 40 chunks are tiled
  with 2 chunks per tile.
* **Sampling**: K=5 at temperature 0.7 / top_p 0.8 / top_k 20; per-chunk label = majority vote, `q` = vote share;
  landmarks = median with spread recorded; cause = plurality (>= K/2 else `unclear`). Optional `--refine` pass shows
  every second frame in a +-3 chunk window around t* when the K votes for t* spread by more than 2 chunks.
* **Routing** (sim only, uses the oracle): every failure goes to the VLM; a success goes to the VLM if it shows a
  re-grasp (>= 2 grasp onsets), a stall (>= 40 idle frames), arm collision, or is > 1.5x the task's median success
  length, plus a deterministic 10 % control sample of clean successes (false-alarm rate). Other clean successes get
  `progress` everywhere with q = 1 without a model call (`source = oracle_default`). On OOPSIE, route on the human
  outcome class instead (clean success skips the VLM; suboptimal / side-effect / failure go through it).
* **Model**: `Qwen/Qwen3-VL-8B-Instruct`, bf16, no quantization, in the LeRobot venv (transformers 5.5.4). One
  prefill per decode round and a K-times repeated KV cache: peak 21.4 GiB, about 20 s per episode at 1x tiles. Plain
  `generate(num_return_sequences=5)` expanded the images 5x before the prefill, spilled into host memory through the
  WDDM driver (25 GiB) and took 250 s per episode. `set_per_process_memory_fraction(0.93)` turns a spill into an
  OOM so the batch can be halved.
* **Two-stage prompting (p5)**: stage 1 is a short greedy call on 2x wrist close-ups at the chunks where the
  gripper is squeezing something (command CLOSE, aperture 1-3.5 cm) that names the held object from the scene
  glossary; stage 2 (the K-sample diagnosis) receives that identification as a stated fact. Reason: on single
  close-ups the 8B model identifies objects correctly, but inside the 28-image diagnosis prompt it drifted into
  "grasped the wrong can" stories about the correct object (p2-p4) and then anchored t* on the first imperfection.
  With the fact injected, full_shift8__t0 ep 0 became "grasped the alphabet soup, lost it near the basket" with
  t* = 11 (oracle: slip in chunk 12) and ep 6 a unanimous grasp failure. Tiles are shown at 1.5x (11k prompt
  tokens, decode in rounds of 3, about 40 s per episode).
* Samples that give a failed episode a single label from start to end are non-answers and are dropped by the
  aggregator when at least two informative samples exist (`k_degenerate` in the record).
* Glossary text was written from `object_gallery.py` renders, not from memory: the alphabet soup asset is a dark-blue
  can and the butter box is red. A wrong glossary (p2) made the model call the correct object "tomato sauce".

## Files

| file | role |
|---|---|
| `common.py` | dataset access, `Episode` view (chunks, frames, non-priv signals), paths (`$FTL_ANNOT` = `$PROJ/annot`) |
| `render.py` | tiles, per-chunk signal table, contact sheet, dense window tiles |
| `prompt.py` | `SYSTEM`, `REFINE_SYSTEM`, LIBERO glossary, `PROMPT_VERSION` (bump on any edit) |
| `schema.py` | pydantic schema, alias normalisation, JSON extraction, per-chunk expansion |
| `backend_qwen.py` | local Qwen3-VL backend; `generate(system, content, k) -> list[str]` |
| `aggregate.py` | self-consistency aggregation, refinement merge |
| `route.py` | VLM / clean routing and default clean record |
| `annotate.py` | resumable driver; one JSON per episode under `annot/<tag>/<dataset>/` |
| `to_labels.py` | `annot/<tag>/labels.parquet`, one row per frame (label, q, cause, landmarks, source) |
| `eval_vs_oracle.py` | scores a tag against a reference tag in the same record format (oracle / human / other VLM) |
| `inspect_records.py`, `zoom_episode.py`, `object_gallery.py`, `montage.py`, `collect_objects.py` | inspection tools |
| `annotate.sh`, `py.sh`, `download_model.sh`, `env_probe.sh` | WSL wrappers (logs in `$PROJ/logs/annotate_<tag>.log`) |

## Usage

```
# render-only check, previews to outputs/annot_preview/<dataset>/
annotate.sh --datasets full_shift8__t0 --episodes 0 --dry-run
# annotate a family (resumable; existing records skipped)
annotate.sh --datasets full_shift8 full_shift12 full_goal full_l90 --refine --tag qwen3vl8b_p3
py.sh inspect_records.py qwen3vl8b_p3 full_shift8__t0
py.sh to_labels.py qwen3vl8b_p3
py.sh eval_vs_oracle.py --pred qwen3vl8b_p3 --ref oracle
```

## Status and next steps

* Tested on 12 full_shift8 failures (tasks 0 and 1), prompt p6/p7: 5/5 valid JSON every time, held object identified
  correctly in all 8 episodes with a grasp (0.95 to 1.0), causes and t* now episode-specific (ep 0: manipulation,
  t* = 12, unanimous; oracle: slip in chunk 12). Test tags under `annot/`: `smoke*`, `p2test`..`p6`, `p7test`;
  delete them before a production run.
* Prompt lessons: (1) an example JSON with concrete numbers was copied verbatim (p5: 11 of 12 episodes had
  t* = 11 and the example's segment boundaries), so the schema example now uses `<chunk>` placeholders;
  (2) any sentence that tells the model what label to expect gets applied everywhere (a "never holds an object"
  fact turned three episodes into failure_inducing from chunk 0); (3) the model rarely fills `recoverable_until`,
  which the recovery-branching oracle supplies anyway.
* Further prompt tuning without ground truth is guesswork. Next component: the oracle segmenter (privileged-state
  rules + recovery branching from snapshots, writing `annot/oracle/...` in the same record format), then
  `eval_vs_oracle.py` on a stratified dev set of about 150 episodes, then the full corpus run
  (about 800 failures + routed successes, roughly 40 s each, resumable, roughly 10 h of GPU time).
* Episodes in which the gripper never holds anything (3 of 12) still come back as `failure_inducing` from chunk 0
  in every sample, with a correct verbal description ("hovers over the blue can, never grasps the cream cheese")
  but no temporal localisation. The aggregator caps q at 0.5 and sets `all_degenerate` for such records so the
  learner down-weights them; the oracle dev set will tell whether this class needs its own prompt.
