# OopsieData teacher traces and Qwen7B SFT

New distillation uses real **OopsieData only**. The old Sol/LIBERO release and
Gemma scripts are historical, not inputs or splits for this pipeline. Settings
live in `configs/oopsie_qwen7b_markdown.json`. New teacher annotations, review
notes, reference annotations, and SFT assistant targets use Markdown.

## Current phase: binary failure segmentation V9, before distillation

The next scale check is the [twelve-episode V9.1 pilot](oopsie_binary_v9_1_twelve.md),
configured by `configs/oopsie_binary_v9_1_twelve_v1.json`. It preserves the V9.1
prompt and supplies every recorded timestamp, packing synchronized camera views
side by side to stay within the API image-count limit. This presentation change
and all twelve fresh teacher responses/repeats are versioned separately from the
original five-episode run. The linked plan describes the conditional 500-episode
collection, 50 held-out validation episodes and student–teacher frame agreement.

The next prompt revision is **V9.1**, in
`scripts/annotate/prompts/binary_failure_v9_1.md`. It adds the OopsieData human
taxonomy as recognition criteria, concrete contrasts for unfinished attempts,
failed acquisition, pauses and recording endings, and explicit failure interval
start/end rules. Its answer format remains the same three-column binary table;
categories and explanations are not returned. The original V9 prompt and its
30 existing responses remain unchanged.

`configs/oopsie_binary_v9_1.json` selects the same five reviewed episodes and
the same all-frame inputs, teachers and three repeats for a controlled comparison
in a fresh `outputs/oopsie_binary_v9_1/` run. The matched rerun uses 30 independent
calls: five episodes, both teachers and three repeats. Image bytes and source
metadata are checked against V9 before collection; only the prompt changes.
V9 remains available in the reviewer on port 8794, and V9.1 uses a separate
reviewer on port 8795. Distillation remains deferred.

The V9.1 rerun completed 30/30 structurally valid responses, estimated at
$1.901176 using the frozen rates. Every teacher/repeat returned the same partition
for each episode: O001, O002, O006 and O007 are all non-failure; O005 is non-failure
`[0,78)` and failure `[78,83)`. The O001 disagreement seen in V9 did not recur.
All earlier V9 requests, responses and user review records remain preserved.
`v9_comparison.md` in the new run lists the exact before/after intervals. Ten
offline checks and browser checks of 102 label/playhead combinations passed.
This is consistency on five recordings, not independently established accuracy.

The V9 experiment deliberately removes action labels, identities, descriptions,
failure categories, recovery fields and uncertainty metadata from teacher output.
The native Markdown answer contains only an episode heading and a table of
`Start frame`, `End frame`, and `Failure` (`Yes` or `No`). Intervals are half-open,
cover the complete recording, and merge adjacent equal labels. The simplified
prompt is `scripts/annotate/prompts/binary_failure_v9.md`; V8 and previous answers
remain unchanged.

`configs/oopsie_binary_v9.json` defines a separate O005/O006 pilot under
`outputs/oopsie_binary_v9_pilot/`. Both complete episodes supply every recorded
frame from every audited camera, with the existing 280 px image maximum side.
There are no clip windows, temporal frame drops, source outcome hints or robot
telemetry. O005 has 83 frames from one camera; O006 has 93 frames from three
cameras, for 362 supplied images across the two episode inputs.

Each of Sol and Astra receives three independent identical requests per episode:
12 generation calls in total, with a $30 run-total ceiling at the frozen rates.
First-pass structural failures and interrupted requests stop collection and are
preserved; they are not automatically repaired or resent. Every request, native
answer, raw response, usage record and source hash is retained internally.

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py prepare --config configs/oopsie_binary_v9.json
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py collect --run outputs/oopsie_binary_v9_pilot --budget-usd 30
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py report --run outputs/oopsie_binary_v9_pilot
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py review --run outputs/oopsie_binary_v9_pilot
```

Preparation requires a fresh output directory; the existing pilot must not be
overwritten. The V9 reviewer is served separately on port 8794 with the existing
`serve_oopsie_review.py` server. It compares Sol and Astra side by side, allows
selection of all repeats, and supports original-video seeking and Markdown review
notes. Teacher annotations themselves contain no explanations or categories.

`report.md` shows every proposed failure interval and pairwise frame agreement
and failure IoU, including comparisons within each teacher. Both-negative pairs
have no failure IoU rather than a misleading perfect failure score. These are
repeatability and agreement measurements, not accuracy against human references.
The first question is whether binary segments are credible and consistent under
video review. SFT and training-target export are deferred until that is established.

The initial V9 pilot completed 12/12 structurally valid responses, estimated at
$0.536559 using the frozen rates. Both teachers returned identical segments in
all three repeats: O005 non-failure `[0,78)` and failure `[78,83)` (15.6–16.6 s),
and O006 non-failure `[0,93)`. This establishes consistency on these two recordings,
not general accuracy. Nine offline tests and browser checks of all four cameras,
repeat selectors, labels, seeking, downloads and responsive layouts passed.
The live reviewer is `http://127.0.0.1:8794/review.html?episode=O005&frame=78`.

The next V9 batch adds O001, O002 and O007 in the separate run
`outputs/oopsie_binary_v9_more_v1/`, configured by
`configs/oopsie_binary_v9_more.json`. All three complete recordings passed token
preflight for both teachers: O001 7,178 tokens, O002 59,147, and O007 8,386.
It supplies all 991 recorded camera frames, retains the frozen V9 prompt and
image settings, and requests three repeats per teacher (18 new calls).

Combine this batch with the accepted pilot for a five-episode reviewer:

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py review --run outputs/oopsie_binary_v9_pilot --supplement-run outputs/oopsie_binary_v9_more_v1
```

The combined view uses byte-identical review copies of the pilot videos and
native Markdown answers; their original manifests, requests, responses and review
acceptance notes are preserved. Each episode retains its source manifest in saved
review notes. Refresh the existing reviewer on port 8794 to see all five episodes. O007
retains its development assignment. The shared binary reviewer now shows labels
for all episodes by default; an explicit global blind-review mode can hide them.
This remains teacher-assisted review, not a blind reference or an accuracy
benchmark. Distillation remains deferred.

All 18 new calls passed structural validation, estimated at $1.339458 using the
frozen rates. O002 and O007 have identical all-non-failure partitions across all
repeats of both teachers. O001 is a counterexample to uniform reliability: Sol
marks failure from frame 33 in repeats 1/2 but no failure in repeat 3; Astra marks
failure from frames 35, 38 and 36 respectively. These are unreviewed predictions.
The combined reviewer exposes all 30 original teacher responses across five
episodes and retains the accepted O005/O006 labels and review record.

## Revised prompting pilot: v3

`configs/oopsie_qwen7b_markdown_v3.json` freezes a new run under
`outputs/oopsie_distillation_md_v3/`. It uses the same ten original recordings,
cameras, image resolution and lab splits, with 10-second windows, one-second
overlap, and a target sampling rate of 4 Hz per camera. Original frame indices
and timestamps are preserved. The per-window cap is 48 frames; preparation fails
rather than silently thinning a window that exceeds the cap. Window selection
does not depend on source failure annotations.

The first collection covers all eight windows of training episodes O004/O005,
with both teachers: 16 requests under the existing $30 run-total ceiling. This is
a targeted diagnostic pilot based on previously reviewed teacher proposals,
not a representative evaluation sample. The other prepared windows remain
ungenerated until the broader continuation is requested.

The new Markdown prompt adds `Uncertain fields`. Failure existence, categories,
timing, action, participant identity, mechanism, final outcome, recovery, severity
and resetability are separate judgments. Any material uncertainty retains the
review flag. A flagged segment receives conservative field-specific loss masks:
only explicitly supported scalar fields remain supervised; flagged narratives,
evidence and uncertainty metadata stay excluded. In particular, uncertain timing
does not automatically remove a supported failure label. Uncertain failure itself
excludes both positive and negative failure supervision and its dependent fields.
Identity-section uncertainty keeps its existing full-section exclusion.

Old outputs retain their original whole-segment masks. New targets preserve exact
returned Markdown; the collator uses the same Unicode exclusion mechanism. The
training and tokenization audit use `has_eligible_segment_targets` for v3, while
`has_unflagged_segment_targets` keeps its literal historical meaning. Teacher
counts refer to segments/windows and can double-count overlapping observations;
they are not counts of distinct physical failures or independent episodes.

All 36 prepared windows passed the input-only Qwen audit: 3,459–13,408 prompt
tokens with room for the frozen 8,192-token output ceiling. No 7B weights were
loaded for that audit. Original teacher outputs and frozen inputs remain intact.

The separate v3 reviewer is served at `http://127.0.0.1:8793/review.html`. It uses
the original videos, bounds playback and annotation timelines to each window, and
shows which judgments need review. It is rebuilt after collection; generated
labels still require semantic video review. Conservative agreement scores retain
whole-segment exclusions, so they do not measure the new partially supervised
failure fields. Overlapping windows must not be presented as independent test
episodes, and predictions are not automatically stitched into full-episode labels.

The first pilot completed all 16 requested responses with no invalid outputs,
estimated at $1.872258 using the frozen rates. Each teacher proposed three usable
positive segments: two failed grasps in O004 and one missed placement in O005.
These are teacher proposals, not adjudicated ground truth. See the native
Markdown labels and `pilot_report.md` under the v3 run for intervals, remaining
uncertainty and direct video-review links. The other 56 prepared teacher requests
were not submitted.

## Review through video

Open [the local video reviewer](http://127.0.0.1:8792/review.html). Start with O001:
both existing teacher traces are available as plain-language cards next to the
original cameras. Play/pause, scrub, step frames, change speed, or click an
evidence citation to inspect its time. The episode selector includes all ten
recordings.

The combined reviewer now includes both teachers for all ten episodes. Sol and
Astra appear in equal-width columns with matching fields aligned. Previous/next
teacher-frame controls move every camera and refresh both teachers' frame
readouts and current-frame citations. A segment description stays the same while
the playhead remains inside that segment; frames without a citation say so.
On narrow phone screens, the comparison stacks vertically for readability.

Record corrections in **Your review notes**, then choose **Save Markdown notes**.
The local server writes a new `.md` file under the run's `reviews/` directory.
**Download Markdown** also saves a browser copy. Notes do not automatically
approve labels or change training masks. No JSON reading is required.

The two original O001 traces stay frozen in the first run. Their downloadable
Markdown annotations are explicitly marked as readable conversions. The new
Markdown-native run is `outputs/oopsie_distillation_md_v2/`, prepared with the
same source identities, cameras and split policy.
The previous two traces are not presented as native Markdown generations.

The user accepted O001 through video review on 2026-10-24 and authorized labeling
O002–O010 with both teachers. That continuation uses the Markdown run, retaining
the original O001 annotations and exclusions. The acceptance record is
`outputs/oopsie_distillation_v1/reviews/O001_user_acceptance_20261024.md`.
It records teacher-assisted review, not independent reference annotation.

Rebuild the combined video reviewer while retaining each episode's source:

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/review_oopsie_video.py --run outputs/oopsie_distillation_v1 --supplement-run outputs/oopsie_distillation_md_v2
```

The primary source retains O001. The supplement supplies the new Markdown
episodes. Both teachers for a given episode stay on one source protocol. The
builder verifies identical original recordings, native cameras, frame grids,
tasks and split assignments, then records per-episode label provenance.

## Frozen pilot

The source is `OopsieData-Submissions/oopsiedata-v0.1` at
`da4b16512b77f7324296a66da7c0067a40539895`. Preparation uses the ten downloaded
episodes and reviewed native camera identities in
`scripts/tacc/oopsie_ten_camera_mapping.json`. It verifies HDF5/video hashes,
native instructions, camera frame counts, and decoded PTS grids. Byte-identical
duplicate cameras are excluded with provenance. Encoded clock checks do not
independently establish physical capture synchronization.

The initial contract is visual-only: task, native camera names/descriptions,
source frame indices/timestamps, and JPEGs. No source outcomes, source failure
descriptions, FLORA predictions/rubrics, or simulator telemetry enter model
inputs. A robot-state extension needs its own validated/versioned contract.

Sample at up to 2 Hz, capped at 32 frames per camera, retaining first/final frames.
The cap can lower the effective rate. Images have maximum side 280 px; geometry,
orientation and letterboxing are preserved. Both teachers and Qwen receive the
same image files and text ordering; Qwen applies its recorded processor budget.
Sparse/low-resolution observations can miss brief events or small objects.
Review pilot quality before scaling, and version any sampling changes.

Both frozen runs contain the same 10 episodes and 626 images:

| Split | Episodes | Held-out grouping |
| --- | --- | --- |
| Train | O001–O006 | Six labs |
| Development | O007–O008 | Princeton_VLL, Princeton_PRPL |
| Test | O009–O010 | UdeM_REAL, UofT_TISL |

The splits hold out entire labs. This is a structural pilot, not a representative
accuracy benchmark. Expanded selections must also keep related recording/session
groups and duplicates together; lab grouping alone does not detect cross-lab
copies. Freeze expanded identities before generation.

## Environment and input audit

Use Python 3.12 from the repository root. This separate environment leaves the
LeRobot/review environments unchanged:

```powershell
python -m venv .venv-oopsie-distill
.venv-oopsie-distill/Scripts/python.exe -m pip install torch==2.11.0+cu128 torchvision==0.26.0+cu128 --index-url https://download.pytorch.org/whl/cu128
.venv-oopsie-distill/Scripts/python.exe -m pip install -r scripts/distill/requirements-oopsie.txt
```

Linux/WSL uses `.venv-oopsie-distill/bin/python` instead. Each training run records
package versions. Collection uses `OPENAI_API_KEY` from the environment or ignored
`.env`; credentials are never included in artifacts.

The student is `Qwen/Qwen2.5-VL-7B-Instruct`, pinned to
`cc594898137f460bfe9f0759e9844b3ce807cfb5`. Defaults: NF4 QLoRA, frozen vision
tower, language decoder rank 16 / alpha 32, LR 1e-4, microbatch 1, accumulation 8,
two epochs, seed 20261023. Input audits download only the processor/tokenizer.
Actual training/generation downloads the 7B weights and requires CUDA.

```powershell
# Preparation requires original downloaded media and the audited provenance.
# An existing run is never overwritten; use --out for a fresh run.
.venv-oopsie-distill/Scripts/python.exe scripts/distill/oopsie_pipeline.py prepare --config configs/oopsie_qwen7b_markdown.json
./scripts/distill/oopsie.ps1 verify
.venv-oopsie-distill/Scripts/python.exe scripts/distill/qwen_oopsie_sft.py audit-inputs --run outputs/oopsie_distillation_md_v2 --out outputs/oopsie_distillation_md_v2/qwen_input_audit.json
./scripts/distill/oopsie.ps1 review
```

The Markdown run and input-audit receipt already exist in this workspace. Use a
new audit `--out` to repeat it. `manifest.json` hashes the configuration, prompt,
camera map, and every JPEG. Changes to evidence/settings require a fresh run.
Historical annotation source fingerprints remain unchanged.

Setup check on 2026-10-23: 21 focused tests passed, including CUDA NF4 backward,
an optimizer update and adapter reload on a small Qwen architecture. All ten
real prompts fit the context cap (2,353–10,711 tokens). O001 has two completed,
schema-valid teacher traces, estimated at $0.081576 combined; both flag its
unresolved final grasp outcome, so its segment stays masked. The other 18 calls
remain pending in the old run. Full 7B SFT has not run. The new Markdown input
audit uses 2,178–10,331 prompt tokens. Its user text and assistant targets are
Markdown; transport/configuration records stay internal to the tooling.

## Teacher collection and review

Collection commands submit paid work. The dollar ceiling applies to the entire
run, including prior/unknown attempts. Stored standard token rates were checked
on 2026-10-23 against the [Sol model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
and [Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra).
Recheck for new runs; estimates are not exact billing guarantees. Input tokens
are counted before generation; requests use frozen input/output caps and stop
on the first failed attempt.

```powershell
# Two independent calls on O001, then inspect the actual answers.
./scripts/distill/oopsie.ps1 collect-smoke -BudgetUsd 30
./scripts/distill/oopsie.ps1 review

# Continue the same run, retaining all existing attempts.
# Current user-authorized continuation excludes the accepted original O001.
.venv-oopsie-distill/Scripts/python.exe scripts/distill/oopsie_pipeline.py collect --run outputs/oopsie_distillation_md_v2 --budget-usd 30 --episodes O002 O003 O004 O005 O006 O007 O008 O009 O010
.venv-oopsie-distill/Scripts/python.exe scripts/distill/oopsie_pipeline.py validate --run outputs/oopsie_distillation_md_v2
./scripts/distill/oopsie.ps1 review
```

Traces retain raw responses, answer text, parsed annotations, request/manifest
hashes, code fingerprints, returned model, usage, costs, and attempt state.
Unknown/failed attempts are never automatically resent. A lock prevents concurrent
collectors. After a crash, inspect journals and confirm no collector is alive
before manually removing a stale lock. Do not erase attempts to force a retry.
Recovery should use a separately recorded run preserving the original failures.

Validation checks complete partitions, chronological action IDs, referent
stability, categories, supplied native camera/frame citations, sampled positive
onsets, original answer integrity and uncertainty consistency. It does not
establish semantic correctness. Review both agreeing/disagreeing cases against
video and preserve unresolved flags. Source episode outcomes are not temporal
failure references. Do not clear flags or force agreement to inflate coverage.

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/serve_oopsie_review.py --port 8792 --directory outputs/oopsie_distillation_v1
```

This serves the existing O001 annotations with all ten original recordings.
For the new Markdown run, rebuild its review with `./scripts/distill/oopsie.ps1
review` and serve that run on another port. The range-capable server supports
video seeking and Markdown-note saving; a plain file server does not provide the
note-saving endpoint. Held-out teacher descriptions/timelines stay hidden until
explicitly revealed. Independent references must be authored before viewing
teacher predictions. The interface records teacher exposure and full-video
evidence conditions in the Markdown notes.

Offline teacher comparison (after both teachers complete the selected split):

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/score_oopsie.py --run outputs/oopsie_distillation_md_v2 --split train --out outputs/oopsie_distillation_md_v2/teacher_agreement_train.json
```

## Export and train

New exports preserve the exact returned Markdown, including Unicode and newline
coordinates. Whole uncertain Markdown sections retain their loss exclusions.


Start with a Sol-only baseline. A separate export can choose Astra per reviewed
episode using `--decisions choices.json`, mapping IDs to
`{"teacher":"astra","reviewer":"actual reviewer","note":"review rationale"}`.
Choosing a teacher is not independent human annotation. Edited adjudications
need a separately versioned dataset; the exporter never silently rewrites an
original teacher answer or asserts human verification.

```powershell
./scripts/distill/oopsie.ps1 export
./scripts/distill/oopsie.ps1 audit
./scripts/distill/oopsie.ps1 smoke
# Inspect finite loss/gradients, memory, checkpoint and held-out generation.
./scripts/distill/oopsie.ps1 train
```

Export/training destinations must be new. Export receipts locate the frozen run
relatively, so ship both directories together. Targets preserve annotation values;
whole uncertain segments and identity objects receive half-open Unicode character
loss exclusions. The collator uses fast-tokenizer offsets and verifies assistant
suffix alignment after native image expansion. Any token overlapping an excluded
character is masked. User/image/padding/control tokens are masked; the native
assistant end token is supervised. Records without eligible segment targets remain
in the export but are skipped for SFT, never converted to negatives.

No silent truncation, image shedding or OOM skipping is used. Over-24,576-token
sequences fail the audit. Revise the frozen input contract rather than drop
arbitrary labels. Token-summed loss projects only supervised positions using
chunked/checkpointed vocabulary logits, with native multimodal position handling.
Adapters/processors are saved; optimizer-resumable checkpoints are not supported.
Six training episodes support a pipeline smoke test, not a useful final model.

## Evaluation

Keep identical evidence for base/adapted Qwen; choose checkpoints on development,
then evaluate once on test. Use `completion.json` for the actual saved adapter.

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/qwen_oopsie_sft.py generate --run outputs/oopsie_distillation_md_v2 --split development --out outputs/oopsie_qwen_md_base_dev
.venv-oopsie-distill/Scripts/python.exe scripts/distill/qwen_oopsie_sft.py generate --run outputs/oopsie_distillation_md_v2 --split development --adapter outputs/oopsie_qwen7b_md_sft_v2/adapter_step_2 --out outputs/oopsie_qwen_md_sft_dev
.venv-oopsie-distill/Scripts/python.exe scripts/distill/score_oopsie.py --run outputs/oopsie_distillation_md_v2 --predictions outputs/oopsie_qwen_md_sft_dev --out outputs/oopsie_qwen_md_sft_dev/teacher_scores.json
```

Scores include schema validity, failure P/R/F1, categories, boundaries and overlap.
Teacher-reference scores are agreement, with provisional-label fractions, not
accuracy. For independent evaluation add `--references /path/to/human_references`.
That directory contains Markdown annotation files and a `references.md` index:

```markdown
# Independent human references

- Kind: independent_human
- Reviewers: actual reviewer identity; optional second reviewer
- Blind to teacher: Yes
- Manifest SHA-256: actual frozen manifest hash

## Episodes

- O007: O007.md | actual annotation file hash
- O008: O008.md | actual annotation file hash
```

Use real provenance, not placeholder claims. Full-episode independent scoring
requires resolved reference segments; unresolved references remain review
artifacts. Record evidence conditions and adjudication. Do not tune on test labels.

## Checks

```powershell
.venv-oopsie-distill/Scripts/python.exe -m unittest discover -s scripts/distill -p test_oopsie_pipeline.py -v
.venv-oopsie-distill/Scripts/python.exe -m unittest discover -s scripts/distill -p test_qwen_oopsie.py -v
.venv-oopsie-distill/Scripts/python.exe -m unittest discover -s scripts/distill -p test_oopsie_markdown.py -v
.venv-oopsie-distill/Scripts/python.exe -m unittest discover -s scripts/distill -p test_oopsie_video.py -v
```

Tests cover frozen inputs, split restrictions, native evidence, Unicode overlap
masks, export fidelity, budgets/interrupted submissions, actual Qwen processor
expansion, native/chunked loss agreement, gradients, frozen vision and adapter
save/reload, exact Markdown targets, native newline/Unicode masks, HTTP video
seeking and append-only Markdown notes. Synthetic tests stay in temporary directories. The small random
Qwen architecture test is not completed 7B SFT; paid traces, human review and
actual 7B smoke results must be reported separately.
