# OopsieData distillation recipe study

The user requested broad baseline, supervised and feedback-loop experiments,
then required confirmation before job submission. Work was paused and explicitly
resumed for the local benchmark and preparation. **Training and cluster
submissions remain unapproved.** The exact
[first-wave plan](../outputs/oopsie_distillation_recipes_v1/submission_plan.md)
and [live status](../outputs/oopsie_distillation_recipes_v1/status.md) distinguish
prepared jobs from started runs. There is no submission approval receipt.

## Data and shared evidence

The unchanged Sol V8.1 collection supplies 394 usable training episodes, 50
development episodes and 49 final-test episodes. Seven responses with invalid
citations stay quarantined across every recipe. Native requests, outputs and
annotations are preserved. The first screening uses a frozen, nested subset of
50 training episodes; it does not claim to train on all 394 yet. Development
uses all 50 episodes; final test is sealed.

Every source timestamp and native camera panel is retained across overlapping
windows. Each 32-frame scored core has up to 8 context frames on either side.
Scored cores partition each episode exactly once, so overlapping context does
not multiply metric counts. Original frame indices and frame rates are kept.
Windowed students do not receive distant episode context; this limitation must
be checked in error analysis before attributing failures to a training recipe.

The fixed model is Qwen/Qwen2.5-VL-7B-Instruct at revision
`cc594898137f460bfe9f0759e9844b3ce807cfb5`, with NF4 QLoRA on the language decoder
and the vision tower frozen. Source camera pixels retain the teacher's 280-pixel
maximum side and packed lossless strips. The Qwen processor's native resizing
and multimodal positions are used; targets are never truncated.

The resumed training-only GPU benchmark on the local 3090 measured:

| Maximum visible frames | Sequence tokens | Peak allocated GiB | Forward/backward/update seconds |
|---:|---:|---:|---:|
| 32 | 8,302 | 15.60 | 11.92 |
| 48 | 11,934 | 19.35 | 15.79 |
| 64 | 15,566 | 22.79 | 31.53 |

The 48-frame setting was selected using the predeclared 21.5-GiB headroom
threshold. The larger case ran but exceeded that threshold. These temporary
benchmark updates were discarded; their losses are not recipe-quality results.
All 1,547 records in the selected export passed the token audit; the maximum was
12,104 tokens under the 32,768 cap. Representative real processor counts matched
the pinned resizing/tokenizer formula exactly.

The Linux runtime uses torch 2.7.0+cu128, transformers 4.57.6, peft 0.18.1 and
bitsandbytes 0.49.2. The local venv inherits the already installed Linux CUDA
PyTorch but overlays its own added dependencies, preserving the original
environment. The initial Windows build lacked FlashAttention and its incomplete
attempt was preserved rather than treated as a benchmark result. A portable
streaming-checksum fallback supports Python 3.10 without changing hash values.

## First-wave comparisons

All trained arms use the same frozen primary binary targets and episode IDs,
40 screening optimizer updates, and a fixed seed. The planned arms are:

| Arm | Supervision | Evaluation |
|---|---|---|
| base | No training | Pretrained Qwen binary output |
| binary | Binary timeline only | Qwen alone |
| joint | Binary timeline plus supported categories/explanations | Binary prompt, Qwen alone |
| categories_aux | Binary task plus category task | Binary prompt, Qwen alone |
| evidence_aux | Binary task plus explanation task | Binary prompt, Qwen alone |
| both_aux | Binary task plus categories and explanations | Binary prompt, Qwen alone |
| binary_compute_control | Extra binary supervision on the auxiliary visual windows | Binary prompt, Qwen alone |
| joint_then_binary | Joint training followed by binary-only training | Binary prompt, Qwen alone |
| failure_balanced | Binary supervision with positive/negative window balancing | Binary prompt, Qwen alone |

Auxiliary targets are only eligible when the entire described failure interval
and its cited frames are visible in the input context. There are 20 eligible
auxiliary windows in this screening export, compared with 604 binary training
windows. This is a limitation on the strength of any explanation-recipe
comparison, not evidence that explanations are ineffective. All existing
teacher explanations remain preserved, including those unsuitable for a local
student window.

Binary-example exposure is matched across ordinary supervised arms. Auxiliary
arms add one weighted auxiliary example per optimizer update; the compute
control adds the same visual exposure using binary targets. Token counts and
GPU time are recorded. The staged joint-then-binary arm keeps the same total
optimizer budget. Training losses with different target lengths are not used
as cross-recipe quality scores.

The first-wave plan contains three bounded local runs and six independent
TACC A100-small GPU jobs, at most two simultaneous TACC jobs. Each GPU job is
capped at two hours and is not automatically requeued. The GPU ceiling is 18
SUs, plus at most 0.143 SU for one CPU environment/weight setup job. The local
group is capped at six hours. There are no new teacher calls. Setup and GPU
job scripts both require a matching approval receipt; none has been created.

## Feedback and later experiments

The binary checkpoint and actual training-pool drafts are prerequisites for:

- Qwen self-review at inference time, preserving drafts and revisions.
- Error replay using the existing independent Sol references, paired with a
  matched continuation control. This tests adaptive sampling with fixed labels.
- Distillation of Qwen self-revisions, with provenance and independent held-out
  diagnostics; self-consistency is not treated as correctness.
- New Sol-assisted review of actual student drafts and correction distillation.
  New teacher requests need a separate concrete review/budget plan.
- Preference or reward training once rejected/accepted pairs or validated
  rewards and rollouts actually exist.

These branches are dependencies in the study manifest, not claims that their
training code has all been implemented or that they have been submitted. They
are not launched automatically by the first-wave approval. Expanding finalists
to 200 and then 394 training episodes and additional seeds also requires a
concrete follow-up plan. Final test remains sealed during recipe selection.

## Evaluation and verification

Development reports include pooled and mean-episode frame agreement, failure
precision/recall/F1, IoU, output validity, coverage, one-to-one matched boundary
error and compute. Invalid or missing output remains unknown; it is not silently
converted to non-failure. Strict agreement counts unknown frames against the
score. Time-capped/incomplete experiments are marked and not ranked as finished.

The always-No development control has 74.24% frame agreement but zero failure
recall/F1. The always-Yes control has 25.76% agreement and 40.97% failure F1.
These are mathematical controls, not model results. Agreement with Sol measures
imitation; independent human review is needed for accuracy claims.

Checks passed for full timestamp coverage, source-preserving clipping,
out-of-context citation rejection, strict invalid-output accounting, episode-first
sampling, boundary stitching, portable checksums, approval gating and generation
time limits. The existing eight Qwen integration checks also passed in the Linux
runtime, including CUDA NF4 training and adapter reload. Shell job scripts pass
syntax checks. No SFT checkpoint or new teacher output has been created.

The auxiliary-supervision idea is motivated by
[Distilling Step-by-Step](https://arxiv.org/abs/2305.02301), whose reported results
are NLP results rather than proof for robotic failure localization. Native input
handling follows the [Qwen processor documentation](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/qwen2_5_vl),
and QLoRA uses [PEFT's quantization workflow](https://huggingface.co/docs/peft/developer_guides/quantization).
TACC limits and rates were checked against its
[Lonestar6 guide](https://docs.tacc.utexas.edu/hpc/lonestar6/).
