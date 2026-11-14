# FLORA experiments: results and next steps

Status snapshot: **2026-10-26, 23:01:40 UTC / 16:01:40 Pacific**. Replacement
ten-episode H100 job **3533752 is PENDING, reason Priority**, with zero runtime
and no assigned start. CPU sampler compiler audit **3533751 completed, exit 0**.
This is a dated observation, not a live queue display.

FLORA Rewarder has run successfully here and produced native dense quality
timelines, segment rationales, and episode-level rubric scores with retained
reasoning. Its accuracy on our failure-segmentation task remains unmeasured.
The original real-data runs have known input/configuration limitations, and the
corrected reference run has not produced completed results. These experiments
justify further controlled evaluation; they do not establish that FLORA broadly
works or fails on OopsieData.

Read the [preserved Oopsie predictions](experiments/flora/2026-10-26/oopsie_predictions.md)
for actual labels and reasoning, the [artifact inventory](experiments/flora/2026-10-26/README.md)
for receipts, and the [TACC runbook](flora_tacc.md) for reproduction and review.
Markdown predictions are **derived conversions of historical JSON generations**.
They are not new model responses or verified human annotations.

## Experiment ledger

| Experiment / job | Conditions | Confirmed result | Interpretation |
| --- | --- | --- | --- |
| Historical LIBERO dense, 3528860 | 12 development episodes; two 40 GB A100s; BF16; TP=2; concurrency=1 | Completed in 21m10s. 3,071 source frames, 22 clips, zero invalid clips. Published weights/code and exact native reconstruction verified. | Successful inference and provenance validation. Simulation integration evidence; no new LIBERO labeling is planned. No human accuracy evaluation. |
| Oopsie rubric pilot, 3529640 | O001–O003; same pinned Rewarder; two A100s; one generic criterion; one sample; 8,192 output / 32,768 context tokens | Completed in 17m15s; all three passed structural checks; complete reasoning retained. | Real-data inference works under this reduced configuration. Not a native-default rubric evaluation. |
| Oopsie dense pilot, 3529899 | Same three episodes; two A100s; TP=2; concurrency=1; original camera order | Completed in 12m19s; all three passed structural checks; native frame labels and rationales retained. | Authentic outputs, superseded for reference performance evaluation because camera geometry/order was not fully verified. |
| Corrected three-episode media audit, 3530162 | Reviewed camera mapping, task-specific rubrics, pinned executable defaults | CPU preflight passed in 30s; original dense outputs reconstructed exactly from saved clip answers. | Confirms media/prompt/defaults/postprocessing checks, not new model inference. |
| Corrected three-episode GPU, 3530163 | Intended H100 reference configuration | Failed in 14m22s during FlashInfer sampler initialization after model loading. Missing Lmod executable, then missing `nvcc`/CUDA path. No completed reference result. | Infrastructure failure; not evidence of semantic model failure. **Do not resubmit this job.** |
| Ten-episode media audit, 3530285 | Ten labs; reviewed camera mappings; original source media | CPU preflight completed in 4m57s. | Technical pilot preparation, not accuracy evaluation. |
| Original ten-episode GPU, 3530286 | Eight-hour H100 cap | Cancelled before starting at the user's request after the three-episode failure. | No inference result; replaced by 3533752. |
| First CUDA repair audit / dependent GPU, 3533746 / 3533747 | CPU build attempted to load CUDA driver | Build/link succeeded but CPU driver load failed (`libcuda.so.1`); dependent GPU cancelled before starting. | CPU nodes cannot verify GPU execution; receipts preserved locally under `attempt1/`. |
| Corrected CUDA audit, 3533751 | Explicit CUDA 12.8 / GCC 13.2; H100 sampler compile-only | Passed in 7s, using compilation cached by the previous attempt. Sampling shared library built/linked. | Compiler path/build validated. GPU execution remains unverified. |
| Replacement ten-episode GPU, 3533752 | New workspace; unchanged ten-episode inputs; native defaults; GPU sampler check before model load | Pending scheduler priority at the snapshot above. Eight-hour cap, at most 48 SUs at the recorded 6 SU/node-hour rate. | Current run to collect. Queue wait is not runtime; cap is not an ETA. |

Durations are whole-job elapsed times, including startup and validation, not
steady-state inference throughput. GPU architectures, settings and inputs differ;
these times are not a speed comparison. Accounting rates are dated run records.

## What the completed Oopsie pilot actually predicted

These counts are computed from saved native frame scores. They describe model
predictions, **not** measured true positives or human task outcomes. Rubric totals
use our generic 0–1 task-progress criterion and are not failure probabilities.

| Episode / task | Duration; frames | Dense failure / suboptimal / normal frames | Native segments | Segments shorter than 0.5s | Rubric total |
| --- | --- | --- | --- | --- | --- |
| O001: pick cup | 2.50s; 50 @ 20 FPS | 50 / 0 / 0 | 1 | 0 | 0.5 |
| O002: put the spoon in the drawer | 22.25s; 267 @ 12 FPS | 0 / 85 / 182 | 55 | 53 | 1.0 |
| O003: pack three grocery objects into a bag | 34.07s; 1,022 @ 30 FPS | 572 / 0 / 450 | 40 | 36 | 0.5 |

For example, O001's native rationale is “the grasp is unstable”; O003 includes a
bag-handle grasp-misalignment rationale. This demonstrates generated localized
judgments and distinguishes them from an all-normal output. Their correctness
and boundary accuracy still require video review. O002's suboptimal spans and
rubric total of 1.0 reflect different prediction modes; disagreement is a review
question rather than evidence that either output is correct.

The temporal fragmentation is a confirmed property of these outputs. In the
separately audited historical LIBERO run, **284 of 309 native segments were under
0.5s, and 292 of 297 label transitions also changed the contributing clip**.
Exact reconstruction with the pinned native parser/stitcher reproduced the
outputs. This implicates cross-window selection as a concrete diagnostic target;
it does not establish that every short segment is wrong or that the underlying
clip judgments are useless. No smoothed output has replaced the originals.

All three Oopsie videos have annotated MP4 exports, source/video hashes and
per-frame timestamp/label-color checks. These checks establish faithful display,
not label correctness. Rubric reasoning is episode-level; written timestamps in
that reasoning are not an independent dense annotation. The corrected reference
viewer does not infer dense timing from rubric prose.

## Input fidelity and limits on conclusions

- **Model:** `nvidia/Flora-Rewarder@7de68d22c4a9decec5ddb7f86ddcaee8f82d3367`.
  The dated audit matched all 12 fetched runtime files and, where recorded, all
  11 weight shards. These observations concern that pinned version.
- **Data:** real `OopsieData-Submissions/oopsiedata-v0.1`, revision
  `da4b16512b77f7324296a66da7c0067a40539895` (dataset card v0.1.1).
  Original task text/media are preserved; source outcome annotations do not enter
  inference inputs. Matching encoded clocks do not prove physical capture sync.
- **Original dense camera problem:** O003 used scene/left-wrist/right-wrist rather
  than left-wrist/scene/right-wrist. O002's three-view positional geometry was
  unverified. Original outputs remain intact, but cannot settle reference accuracy.
- **Corrected cameras:** O001 exterior-left then wrist, with the byte-identical
  right view excluded; O002 exterior `image` then `wrist_image`, with the ambiguous
  extra exterior view omitted from dense input; O003 left-wrist, scene, right-wrist.
  Rubric inputs keep all distinct views with individual descriptions. O002 changes
  camera selection as well as order; the overall rerun is not a single-factor ablation.
- **Reference defaults:** dense BF16, TP=1, concurrency=8, greedy, 640 output /
  16,384 context tokens; rubric BF16, TP=2, concurrency=8, nine samples with native
  medoid selection, temperature=1, 20,480 output / 98,304 context tokens.
  Executable rubric sampling is 2 FPS capped at 166 frames per camera. The model
  card instead describes 1 FPS / 82 frames / 32,768 context; this run follows the
  pinned executable batch defaults, not both conflicting descriptions.
- **Selection:** the ten-episode run spans UT_RobIn, Araya, Stanford_REAL, Armnet,
  Berkeley_RAIL, Enatic_OpenArm, Princeton_VLL, Princeton_PRPL, UdeM_REAL and
  UofT_TISL. Selection was based on media availability and technical checks, not
  balanced failure coverage. Three candidates were excluded for timing/frame-state
  mismatch. Ten labs do not make this a representative benchmark.

The [pinned batch instructions](https://huggingface.co/nvidia/Flora-Rewarder/blob/7de68d22c4a9decec5ddb7f86ddcaee8f82d3367/batch_utils/README.md)
and [rubric implementation](https://huggingface.co/nvidia/Flora-Rewarder/blob/7de68d22c4a9decec5ddb7f86ddcaee8f82d3367/batch_utils/rubric_reward.py)
identify the implementation being reproduced. Researcher-authored task rubrics
are inputs to this experiment, not NVIDIA ground truth.

## Further experiments, in priority order

| Priority / question | Experiment | Evidence to save / decision enabled |
| --- | --- | --- |
| 1. Does the repaired reference run complete? | Collect 3533752; verify GPU sampler, H100s, weight/input/code hashes, actual arguments, all ten dense results and nine rubric samples each. Do not submit duplicates or resubmit the separate three-episode job. | Exit state, logs, receipts, raw answers, structural checks and video review. A passed CPU compile alone is insufficient. Any partial dense results from a later rubric failure must be recorded explicitly as partial. |
| 2. Are failures actually identified? | Human-review all ten videos first. Freeze the binary failure definition and a reviewed subset containing clear failures, recoveries and clean negative intervals. Record ambiguous/occluded spans separately. Add fresh real Oopsie episodes if the ten lack positive cases. | Time-aligned human intervals plus Markdown adjudication. Measure failure precision/recall, false positives on clean spans, temporal overlap and onset/offset errors on observable spans. Report counts and per-episode results, not only a pooled score. |
| 3. Is input geometry responsible for changes? | On the same real episodes, hold code, settings and camera set fixed while comparing original versus reviewed order. Treat O002's two-versus-three-camera change as a separate camera-selection experiment. | Per-clip and stitched outputs with identical media hashes; human-adjudicated differences. A before/after with several changed factors cannot isolate camera causality. |
| 4. Are clip judgments better than the stitched timeline? | Compare overlapping native clip quality strings/regions against human events; trace which window supplies each frame. Evaluate any smoothing or consensus adapter in a new derived run. | Raw native baseline plus separately versioned adapter results; boundary errors, fragmentation and short-failure recall. Avoid improving apparent stability by deleting genuine brief failures. |
| 5. Does rubric design/sample count help? | Separately compare generic versus task-specific criteria with settings held fixed, then one versus nine samples with criteria fixed. Review selected output and sample disagreement. | Raw sample scores/reasoning, costs, completion rate, human outcome judgments. Episode-level success does not substitute for failure-segment recall. |
| 6. How does it compare with Sol/Astra? | Use the same reviewed real episodes, task text, camera evidence and failure definition. Disclose each method's temporal sampling. Compare full episode coverage and a matched evidence condition where practical. | Blinded human review and per-method failure metrics. Report model agreement separately from accuracy; other teachers are not ground truth. |
| 7. Is action segmentation/captioning useful independently? | Run a small new real-data TempSeg/Captioner feasibility pilot with supported camera profiles, then human-review reach/grasp/transport boundaries and captions. | These components were prepared but **not run** in this project. Rewarder findings do not establish their strengths or weaknesses. Intent captions do not prove physical success. |
| 8. Which outputs are fit for distillation? | After human evaluation, freeze a held-out real-data split and a documented adapter from native failure/suboptimal/normal to our binary target. Compare clear-failure-only versus an explicitly adjudicated treatment of suboptimal behavior. | Precision/coverage tradeoff, boundary quality, ambiguous-span masks, training eligibility and downstream held-out student evaluation. No automatic promotion of current outputs to training labels. |

For binary review, use the user's human-annotation principle: a failure segment
is a continuous interval of bad actions that do not progress toward the task;
separate intervals when good actions resume. Mark the earliest observable failure
through recovery, another distinct failure, or the end. A failed episode need not
contain a localized failure segment; a successful episode can include retries,
collisions or other bad-action intervals. Clarify ambiguous stalling/suboptimal
cases before scoring. Native class 2 is not automatically either binary class.

The next decision should come from the corrected real-data outputs plus human
review. Current evidence establishes successful FLORA inference and a reproducible
timeline issue; it leaves failure accuracy, best rubric, cross-embodiment coverage,
H100 equivalence, online detection, and distillation usefulness open.
