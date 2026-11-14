# Sol V8.1: 500-episode Batch collection

The user authorized this run after choosing 500 total episodes and one Sol
response per episode. The collection is running under
`outputs/oopsie_rich_failure_v8_1_500_batch_v1/`. See its generated
[live status](../outputs/oopsie_rich_failure_v8_1_500_batch_v1/status.md) for current
preparation, preflight, remote Batch and validation counts. Preparation is not a
claim that generation requests have already been submitted.

## Frozen scope

- Real OopsieData release revision `da4b16512b77f7324296a66da7c0067a40539895`.
- 500 episodes: 400 training, 50 development, 50 final test.
- `gpt-6.1-sol`, low reasoning, one request per episode. No Astra requests.
- Unchanged V8.1 prompt, SHA-256
  `a665f69f615c5c84cfb07a95d4fdbdd90bd2207d09cf10e60b7da1ac7caa32da`.
- Native Markdown binary timeline, plus taxonomy categories and short
  frame/camera-grounded explanations for each failure interval.
- Every recorded timestamp and distinct native camera view is retained.
- Maximum generation budget **$75**, enforced before any batch submission.
- No student training is started by this collection.

The full accessible release has 10,677 episodes, an average encoded episode
duration of 22.3868 seconds, and 66.3957 hours when each episode is counted once.
Those are full-release measurements, not the duration of this selected corpus.

## Selection and split

`selection_plan.json` freezes seeded candidate and reserve ordering before any
teacher labels. Selection round-robins contributing labs and shuffles within each
lab, using structural metadata only. The twelve reviewed pilot episodes and exact
duplicate multicamera video sets are excluded. This lab-balanced engineering
corpus is not a proportional random sample of the full release.

Development labs are Princeton_IRoM and Princeton_PRISM. Final-test labs are
CMU_Intent, Stanford_Iris, UPenn_PAL and Stanford_MSL. Training uses other labs.
These held-out labs were not in the reviewed twelve. Final selections must have
no lab overlap across splits.

The input-feasibility scope is 2–1,500 recorded timesteps and 1–4 native cameras.
Videos are decoded and checked against the recorded timestep count, uniform
zero-based timestamps and shared camera frame rate. Technically incompatible
recordings are documented and replaced in the frozen reserve order. No source
outcome annotation is read for selection, supplied to the teacher, or used to
replace a recording. `selection.json` and the final manifest freeze the 500
accepted episodes before any generation starts.

## Evidence and Batch transport

The per-camera preprocessing matches the pilot: maximum side 280 pixels,
LANCZOS resizing and JPEG quality 95. Its decoded RGB pixels are packed into one
synchronized camera strip per source timestep. Strips use lossless WebP, retaining
the same pixels while reducing the Batch upload size. Native MP4 and HDF5 bytes
are preserved with release hashes. Native camera identifiers are supplied without
invented geometric roles. Exact duplicate camera recordings are documented and
omitted.

Most requests contain inline lossless strips. If a complete episode would exceed
the Batch file allowance, only enough exact images are uploaded through the Files
API and referenced by file ID; timestamps, order, dimensions and pixels are kept.
No frame is removed to fit a request.

Each frozen request gets an actual input-token count. The budget ceiling reserves
cache-write input pricing and all 8,192 allowed output tokens, including the
long-context pricing multiplier when applicable. Cache hits are not assumed.
Batch files are under 190 MB and one million input tokens each; the controller
keeps at most 2.5 million input tokens enqueued remotely at once.

The submission journal is written before each billable Batch create request.
Completed, invalid, failed or uncertain generation requests are not automatically
resent. Raw Batch output records, response objects, usage, native Markdown and
validation diagnostics are preserved. A failed batch stops new submissions for
inspection.

## Review and operation

The controller automatically collects terminal Batch outputs and publishes a
derived video reviewer on port 8800 with readable, time-aligned failure colors,
categories and explanations. It uses one Sol panel, with labels shown on every
split by default and a persistent viewer-wide optional blind mode. It does not
display or claim repeat agreement for a one-call collection. Existing twelve-
episode reviewers and all their native artifacts remain unchanged.

The status monitor schedules `scripts/distill/check_binary_review_browser.py`
against the ordinary reviewer URL after collection, covering every episode and
available response, navigation, reloads, visibility, simulated label arrivals and
frame stepping. Browser results are saved inside this run. Until that report
passes, broad browser verification remains pending.

Six offline runner checks passed: deterministic lab balancing, all-frame request
construction, cache/long-context cost reserves, refusal to resend a journaled
submission, native-output preservation and interrupted-ingest recovery, and
rejection of unknown/duplicate Batch results. The new viewer's JavaScript also
passed a syntax check. Structural validation of annotations does not establish
label accuracy; these outputs remain teacher proposals for human review.

Read-only current status: `status.md`, `pipeline_status.json`, `queue_status.json`
and `collection_summary.json` inside the run. Do not start a second worker or
resubmit a shard just because a result is delayed. Inspect worker locks and
submission journals first.

Preparation, token preflight and the automatic queue were launched on 2026-10-28
UTC (2026-10-27 Pacific). Background logs and versioned code snapshots are kept
with the run. API pricing and limits were checked against the
[Batch documentation](https://developers.openai.com/api/docs/guides/batch),
[image input documentation](https://developers.openai.com/api/docs/guides/images-vision)
and [Sol model pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol).
