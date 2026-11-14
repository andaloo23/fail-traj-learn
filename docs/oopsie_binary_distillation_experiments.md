# Binary failure distillation experiments

## Full-data first wave, 2026-10-28

The user approved submission of the full-data first wave: pretrained Qwen plus
eight SFT recipes, using **400 train / 50 development / 50 sealed test** episodes.
The [full-data launch plan](../outputs/oopsie_distillation_full_v1/submission_plan.md)
supersedes the earlier 50-training-episode screening proposal. Execution and job
receipts live under `outputs/oopsie_distillation_full_v1/`.

The ordinary SFT schedule is two full passes (2,688 optimizer updates). The
failure-balanced arm first covers every training window and then balances
failure/non-failure replay within its second-pass budget. Every binary source
timeline is valid; invalid auxiliary citations on six training episodes are
excluded from auxiliary targets while retaining their binary labels. Only 168
training windows contain complete, cited failure intervals suitable for the
auxiliary tasks; this limits what those comparisons can establish.

The approved launch ceiling is 291.893 TACC SUs, below the stated 300-SU cap.
New teacher calls: zero. Final-test evaluation and automatic feedback-loop runs
are disabled. Consult the full-data status and submission receipts for actual
queue state; the screening study remains preserved and blocked from launch.

## Screening preparation, superseded

The [recipe study](oopsie_distillation_recipe_study_v1.md) now has frozen shared
targets and screening exports, a completed local GPU benchmark, token/coverage
audits, guarded training/evaluation entry points and concrete job scripts.
The local benchmark is complete. Its 50-episode screening job plan was superseded
before submission; it is not the full-data job plan approved above.

## Authorized 500-episode collection, 2026-10-28 UTC

The user selected 500 total episodes, one Sol V8.1 response per episode, and a
400/50/50 train/development/test allocation, then authorized execution. The
[Batch collection](oopsie_rich_failure_v8_1_500_batch.md) now runs preparation,
token preflight, automatic budgeted submission and result collection. Its
[live status](../outputs/oopsie_rich_failure_v8_1_500_batch_v1/status.md) distinguishes
prepared candidates from remotely submitted requests and returned labels. The
generation budget ceiling is $75. No student training has started. Statements
below about collection not having started describe earlier planning stages.

## Starting point, 2026-10-27

The user reviewed the twelve-episode V9.1 pilot and said: "all 12 sol annotations
look good. lets move on." This records approval of the Sol pilot for proceeding
to distillation experiments. It does not invent individual browser review notes,
claim every repeat was separately adjudicated, or approve Astra as a reference.

Native run: `outputs/oopsie_binary_v9_1_twelve_v1/`. Preserve its requests,
responses, annotations and old split metadata. A new experiment manifest assigns
the reviewed recordings to training/debugging; they are not fresh final evaluation
data. Three repeats do not make twelve recordings into thirty-six examples of
independent generalization.

Start with **video/task -> binary Markdown segments** supervised fine-tuning
(SFT), using Qwen2.5-VL-7B-Instruct and Sol targets. Label-only describes the
assistant target: the student still receives visual evidence and the task.
No additional teacher collection or GPU training has been launched by this plan.

The subsequent requested [Sol V8/V9.1 paired pilot](oopsie_sol_v8_v9_twelve.md)
has now collected twelve rich OopsieData Markdown responses, reusing all saved
V9.1 Sol outputs and making no Astra calls. The rich labels have 81.12% pooled
frame agreement with V9.1 repeat 1, including many V8 review-flagged spans. The
user judged V9.1 better for failure recognition. The approved V9.1 targets remain
the binary baseline. The next candidate is [V8.1 rich failure annotation](oopsie_rich_failure_v8_1.md),
which preserves V9.1's recognition/boundary rules and adds categories/explanations
after the binary table. Its Sol-only twelve-episode trial now has all 36 responses:
9/12 episodes have exact binary 3/3 agreement, 96.12% of frames are unanimous, and
pooled agreement with the preselected V9.1 repeat 1 is 96.63%. O004/O008/O012 have
repeat disagreements; O009 has category disagreement despite identical binary
labels. These are pilot consistency/teacher-agreement measures, and the enriched
outputs still need human review. No 500-episode collection or GPU training has started.

## Parallel execution and shared collection

The user subsequently asked to investigate the branches in parallel and avoid
redundant API collection. Parallelize independent work and launch experiments
as their inputs become ready; the stages below describe dependencies, not a
requirement to wait for every preceding experiment to finish.

Use one episode corpus and one frozen split manifest, with versioned target
views. Label-only, auxiliary evidence and correction training do not need separate
sets of 500 videos. Keep a common immutable evaluation reference even when
training targets differ. A revised target is not silently substituted into the
reference for the method that produced it.

Two collection options have different costs and scientific interpretations:

- **Exact V9.1 labels:** collect the unchanged binary request once per episode;
  request auxiliary evidence separately on the training subset. This preserves
  the established label-generation protocol but rereads video for evidence.
- **Joint collection:** pilot a new versioned Markdown response containing binary
  labels plus brief frame-grounded evidence. Review it against the approved
  twelve before scaling. From the same native response, produce explicitly
  derived label-only and label-plus-evidence training views. Both recipes then
  share identical binary targets and one teacher video pass. Adding evidence can
  change label judgments, so this is a new teacher protocol, not native V9.1.

Joint collection is the economical default proposal if its small pilot passes;
the V8.1 pilot implements a candidate and awaits human review before bulk collection.
Collecting evidence after supplying
fixed labels is another auxiliary-data option, but describes post-hoc evidence,
not a recovered internal reasoning trace. Keep evaluation generation independent
of student predictions and reserve additional blind human checks.

For an illustrative 500-episode one-call-per-episode joint collection:

| Work | Sol API calls | Dependencies |
| --- | --- | --- |
| Shared labels and evidence | 500 | Accepted joint protocol and frozen source/split |
| Label-only vs auxiliary training, multiple seeds | 0 additional | Shared collection and working binary trainer |
| Qwen draft and self-review | 0 additional | A chosen Qwen checkpoint; local GPU inference |
| Sol reviews 100 selected training-pool Qwen drafts | 100 additional | The actual drafts being reviewed |
| Qwen training on accepted corrections | 0 additional | Reviewed corrections |

This example is 600 Sol calls, not 500 calls per training recipe. It excludes
pilot checks, extra teachers/repeats, failed-request handling and additional loop
rounds. Episode calls become window calls if the teacher input protocol needs
windowing. With exact V9.1 collection plus separate evidence, the base cost is
500 label calls plus one evidence call per selected training episode instead.
Count actual image/input/output tokens, not calls alone, when budgeting.

Once the baseline checkpoint exists, Qwen self-review and Sol review can consume
the same frozen draft predictions in parallel. Train label-only and auxiliary
branches concurrently if GPUs permit. Teacher-correction training can start as
accepted corrections arrive. Base-Qwen draft diagnostics can begin earlier, but
must be labeled separately from reviews of the trained checkpoint.

A correction review can be reused when its exact evidence, draft and review
instruction match. Different checkpoints or loop rounds produce different drafts;
their teacher reviews generally require new calls. Already reviewed corrected
labels can still be shared as static training targets, but do not represent a
new on-policy review of a different student's behavior. Keep the review budget
equal when comparing iterative methods.

Independent offline teacher requests can use the
[Batch API](https://developers.openai.com/api/docs/guides/batch), which documents
50% lower costs and a 24-hour completion window. Verify model and image transport
support before submission; the current largest inline pilot request exceeds the
200 MB Batch input-file limit, so frozen transport cannot simply be copied.
Prompt caching may reduce repeated input cost when eligible exact prefixes match,
but budget without assumed hits and inspect recorded usage; see
[official prompt caching guidance](https://developers.openai.com/api/docs/guides/prompt-caching).

## First deliverable: a working baseline

1. Add a binary Markdown export, parser-backed student generation and scoring
   path. The current `qwen_oopsie_sft.py` has reusable processor, loss masking and
   QLoRA infrastructure, but its existing export/generation contract is for the
   richer schema. Its configuration also describes older sampled evidence.
2. Freeze one canonical target per episode before looking at student results.
   Proposed starting rule: Sol repeat 1, with disagreements between repeats
   flagged for review. Do not silently majority-vote boundaries or select the
   repeat that makes the student score best. Record target hashes and provenance;
   corrections are versioned derived targets, never overwritten native outputs.
3. Audit native Qwen processor token counts and available target capacity across
   all twelve full-rate recordings. Benchmark forward/backward memory and speed
   on short, medium and long feasible examples before choosing a run size. Report
   peak VRAM, processed input tokens/second and optimizer step time.
4. If full episodes do not fit, version a shared student evidence adapter. Prefer
   overlapping windows retaining every source timestamp, with surrounding context
   and non-overlapping scored cores. Keep original frame indices and cameras;
   freeze deterministic stitching and coverage checks. No silent truncation or
   return to isolated sparse frames. Windows whose labels require unavailable
   episode context need a documented context strategy or exclusion with coverage
   reporting; copied whole-episode labels are not automatically learnable locally.
5. Run unadapted Qwen on the same evidence, then deliberately overfit a small
   approved training subset containing both Yes and No intervals. Confirm free
   generation, boundaries and parsing, not merely decreasing teacher-forced loss.
   This checks the pipeline; it is not evidence of generalization.

Freeze the evidence adapter before comparing training recipes. Input resolution,
camera packing and window length are separate experiments, not hidden differences
between label-only and rationale training.

## Controlled comparisons

| ID | Training | Inference | Question |
| --- | --- | --- | --- |
| A | None; pinned pretrained Qwen | One binary prediction | What can the base student already do? |
| B | Approved Sol binary targets only | One binary prediction | How much does ordinary SFT help? |
| C | Same B labels plus a separate auxiliary visual-evidence task | Binary prediction only | Does grounded intermediate supervision help? |
| D | Same checkpoint as B | Draft, then Qwen re-watches the evidence and revises once | Does Qwen self-review help at extra inference cost? |
| E | Same checkpoint as B | Qwen draft, then Sol reviews evidence and proposes a correction | What does teacher-assisted inference add? |
| F | B training set plus accepted teacher corrections on training-pool student errors | Qwen alone, one prediction | Can we train away the need for Sol review? |

Build the shared baseline infrastructure first. Prepare C's auxiliary data in
parallel with A/B; train B and C concurrently once their shared evidence and
targets are ready. Run D and E in parallel on the same frozen B drafts, and start
F after its training-pool corrections arrive. Development inference diagnostics
do not become F training data. The parallel schedule above supersedes the
earlier suggestion to complete each recipe in sequence.

For C, prefer short observable evidence, such as an empty gripper moving away
while the target remains, with frame references and counterexamples from clean
behavior. Coordinate with the teammate studying explanations; this does not
expand the deployed binary label schema into categories. Request evidence as a
separate versioned task with its own prompt. Keep the approved binary target
fixed. If new teacher labels differ, review and version them separately.

Use auxiliary-task training so binary inference does not require generating long
explanations. An evidence-then-label output can be a later independent comparison.
Keep binary-example exposure matched between B and C; also report total tokens
and GPU time, and add an equal-compute B control before attributing a gain solely
to richer supervision. Use matched seeds and multiple seeds for finalists.

Rationale supervision improved smaller models on NLP benchmarks in
[Distilling Step-by-Step](https://arxiv.org/abs/2305.02301). That motivates C;
it does not establish a benefit for robot failure localization.

## What counts as a trace

Existing records contain exact inputs, final labels, transport responses and
opaque reasoning items. They contain no readable reasoning targets. Encrypted
content is neither text supervision nor evidence of what intermediate judgments
were correct. Never supply teacher answers as part of the student's video input.

The API can provide opt-in reasoning summaries where supported, but they are
summaries, not raw internal reasoning. See the
[official reasoning documentation](https://developers.openai.com/api/docs/guides/reasoning#reasoning-summaries).
Any summary collection belongs in a new run and should be evaluated separately
from deliberately requested, frame-grounded evidence. Neither is guaranteed to
be a faithful explanation of the model's decision.

Correction traces for F are another artifact: video/task, student draft, teacher
review, accepted corrected labels and provenance. They can support a later
revision-model experiment. Initially train video/task -> corrected labels so the
resulting student works without a teacher or an externally supplied draft.

## Two distinct loops

**Training loop:** Qwen predicts on the training pool; Sol reviews original
evidence and candidate mistakes; accepted corrections join training; Qwen is
retrained; evaluate on unchanged development references. Sample some apparently
confident/easy predictions too, since disagreement-only selection can miss shared
errors. Show Sol the evidence independently before exposing Qwen's draft where
practical to measure anchoring. Teacher disagreement is a review candidate, not
an automatic student mistake. Never feed development/final-evaluation corrections
back into training.

Compare F against adding an equal number of randomly selected Sol-labeled
training episodes, with teacher tokens/cost recorded. Otherwise more labeled data
could explain the improvement attributed to the loop. Start F from B for both
controls and keep the update schedule matched.

**Inference loop:** Qwen predicts, then Qwen or Sol revises. First use a fixed
two-pass protocol, preserving drafts and revisions. Score correct-to-incorrect as
well as incorrect-to-correct changes. Qwen self-review may improve visual checking,
but agreement with itself is not an independent correctness signal. Repeated
self-training on its own unverified labels is a separate later experiment with
teacher/human-checked diagnostics and an abstention policy.

E is a teacher-assisted system, not proof that Qwen alone learned the skill.
F succeeds only if the updated Qwen improves when run without Sol at inference.

## Data, evaluation and scale

Use the twelve reviewed episodes for engineering and initial training. Acquire
fresh episode-disjoint development recordings before choosing a recipe. Group
related sessions and duplicates before splitting; all windows/repeats of an
episode remain together. Freeze teacher references independently of the evaluated
student. Include clean negatives and genuine positive intervals, and human-check
failure-containing references. Report any deliberately balanced diagnostic set
separately from the natural evaluation distribution.

Start the learning curve with approximately 50 training episodes, then 200, then
the full training allocation if development results justify it. Do not collect
every expensive auxiliary target up front. B and C must use the same episode
subset when compared. Existing reviewed examples can be included in that training
allocation; do not count repeats or windows as new episodes.

The earlier 500-total versus 500-training question remains unresolved. One
possible **500-total** allocation is 400 train / 50 development / 50 final
evaluation, rather than using the final fifty repeatedly for recipe selection.
This is a proposal, not a newly frozen split. If the user wants 500 training,
reserve development and final evaluation in addition. Choose identities and
grouping before collection.

Report frame agreement (pooled and mean episode), failure precision/recall/F1,
failure IoU, boundary error with a predeclared matching rule, invalid-output rate,
coverage and an always-No baseline. Count source timestamps once, not per camera;
do not turn invalid output into No. Pair results by episode and use episode-level
uncertainty, since adjacent video frames are correlated. Track inference latency,
teacher calls/tokens and GPU hours. Use a fixed annotation rule for ambiguous
human-reviewed boundaries and disclose masking or tolerance separately.

Select recipes on development results, prioritizing real failure detection over
high agreement from dominant No frames. A recipe wins when its improvement is
consistent across episodes/seeds and worth its measured cost. Open the final
fifty only after recipe selection. Agreement with Sol measures imitation; a
human-reviewed reference is needed to claim actual annotation accuracy.
