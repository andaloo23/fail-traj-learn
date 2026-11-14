# Sol / Astra attribution audit

Checked 2026-11-13, after the repository scope cleanup.

**The existing 50-episode development presentations use Sol annotations. Their
visible Astra label is a historical display alias, not the generating model.**
A video-only viewer could reasonably assume Astra. A reader or agent inspecting
the repository should identify Sol and explain the mismatch; the source code,
collection guide, manifests, and MP4 metadata make it explicit. This is an
inference from inspected evidence, not a prediction of every agent's answer.

| Artifact | Visible/display name | Actual teacher |
| --- | --- | --- |
| Joint Qwen comparison, native speed and 4x | Astra | `gpt-6.1-sol` |
| FLORA comparison, 4x | Astra | `gpt-6.1-sol` |
| Three-way quantitative report | Astra, explicitly documented as an alias | `gpt-6.1-sol` |
| Historical public Sol V8 500-episode release | Sol | `gpt-6.1-sol`; separate simulator-derived corpus |
| New Corral V8.2 pilot preparation | Astra | Configured for `gpt-6-astra`; no completed native annotations found locally at this audit |

## Evidence checked

The real OopsieData source for the development presentations is
`outputs/oopsie_rich_failure_v8_1_500_batch_v1/`. Its
[collection protocol](oopsie_rich_failure_v8_1_500_batch.md) specifies Sol.
For **all 50 development episodes**, the saved attempt, native response, and
original Batch response identify `gpt-6.1-sol`. Annotation, response, and Batch
record SHA-256 checks matched their saved receipts. The study's source-manifest
hash also matched.

All source-prediction hashes in the Qwen presentation matched. The quantitative
comparison uses those same native teacher annotations; all 50 annotation hashes
matched its provenance map. The MP4 checksums for the native-speed Qwen video,
its 4x version, and the FLORA 4x video matched their export receipts. Each MP4's
comment explicitly identifies the preserved teacher as `gpt-6.1-sol`. The saved
Qwen 4x preview visibly labels that teacher panel Astra.

The following committed code makes this discoverable even without local outputs:

- [Joint Qwen exporter](../scripts/analysis/export_teacher_joint_side_by_side.py)
  reads `_sol_r01/annotation.md`, records `teacher_source_model`, and writes an
  explicit display-alias explanation.
- [FLORA exporter](../scripts/analysis/export_teacher_flora_4x.py) visibly uses
  Astra while recording `gpt-6.1-sol` and `teacher_display_name_is_alias=True`.
- [Quantitative input builder](../scripts/analysis/prepare_astra_qwen_flora_comparison.py)
  reads native Sol annotations and records `teacher_actual_source='gpt-6.1-sol'`.
- [Public release metadata](../datasets/sol_v8_distillation_500/release.json)
  explicitly records its Sol teacher; this is a different, historical corpus.

The local presentation directories are
`outputs/astra_joint_presentation_50_20261109_v1/`,
`outputs/astra_flora_presentation_50_20261111_v1/`, and
`outputs/astra_qwen_flora_quantitative_20261112_v1/`. These generated artifacts
are ignored by Git. A detailed local check receipt is
`outputs/teacher_attribution_audit_20261113.json`.

## Clear wording for sharing

> Initial prompt testing and the existing distillation experiments used Sol.
> Some earlier presentation videos displayed those Sol annotations as Astra.
> We now plan a separate Astra labeling run; those existing results remain Sol results.

For those existing videos, use **Sol (`gpt-6.1-sol`)** as the teacher label in a
corrected, versioned presentation. Reserve Astra for outputs actually generated
by Astra. Similar label behavior does not change which model produced the labels.
The advisor's requested switch is a future collection decision, not a change to
existing teacher provenance. Older genuine Sol/Astra comparison runs should keep
their own recorded model identities.

This audit preserves existing presentations, teacher requests/responses, review
notes, and source labels. It does not regenerate videos, make new teacher calls,
or start training. The [Corral Astra pilot](corral_astra_rich_failure_v8_2.md) is
separate; preparation alone does not establish completed Astra labeling.
