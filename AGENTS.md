# Repository scope

- Keep labeling, human review, distillation, and evaluation pipelines.
- Preserve actual teacher model identity from frozen requests/responses; display
  aliases must never be treated as evidence that another model generated labels.

# Current labeling prompt

- When asked for the latest or current labeling prompt, use
  [rich failure V8.2](scripts/annotate/prompts/rich_failure_v8_2.md).
  This is the authoritative default for new rich OopsieData labeling, even if
  older README or runbook sections describe another protocol as current.
- Its runner is `scripts/distill/corral_astra_v8_2.py`; the workflow and schema
  are documented in `docs/corral_astra_rich_failure_v8_2.md`.
- V8.1 and atomic V8 are historical protocols. Binary V9.1 is a separate,
  binary-only workflow; use it only when that output is requested. The older
  V10-V15 taxonomy experiments are a separate version series, not successors
  to rich V8.2. Preserve these prompts for reproduction rather than selecting
  them as the latest prompt based on their version numbers.

# Current project scope and annotation preferences

- Use real OopsieData for new labeling, distillation, and evaluation work.
- The intended teacher for new rich-labeling runs is Astra (`gpt-6-astra`), as
  configured by the V8.2 runner. Make new teacher calls only within explicitly
  requested run scope. Existing outputs retain their recorded model identity;
  this direction does not relabel prior results or authorize a new collection.
- Distillation experiment runs require the user's confirmation of the concrete
  recipe/job plan before submission. Do not automatically launch the prepared
  sweep or start further local GPU benchmarks/training without that confirmation.
  The user stopped the initial local benchmark on 2026-10-28; no distillation
  cluster jobs had been submitted. Later explicit approval authorizes its stated
  scope without requiring repeated confirmation for the same action.
  The user subsequently resumed the local benchmark/preparation; the requirement
  to confirm the concrete training submission plan remains in place.
- The user wants Markdown for new VLM annotation responses, human review notes,
  and SFT assistant targets. Keep operational manifests and API transport formats
  internal; do not make the user read JSON to review labels.
- Provide video playback with readable, time-aligned annotations for human review.
- Preserve existing frozen requests and teacher outputs. A format or prompt change
  belongs in a new versioned run. Label readable conversions of old outputs as
  derived artifacts rather than native Markdown generations.
- Binary teacher reviewers show labels for every episode by default, regardless
  of train/development/test split. Optional blind review is an explicit viewer-wide
  choice that persists across episode navigation and reloads. Do not use a
  special episode link as a substitute for fixing shared reviewer behavior.
- For binary reviewer changes, run `scripts/distill/check_binary_review_browser.py`
  against the ordinary viewer URL and cover every available episode/repeat,
  navigation, reloads, label arrivals, visibility mode and frame stepping before
  reporting a general fix. Preserve native requests, outputs and review notes.
