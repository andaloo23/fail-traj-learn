# FLORA experiment evidence, 2026-10-26

Start with the [results and experiment plan](../../../flora_results.md). Read
[Oopsie predictions](oopsie_predictions.md) for time-aligned native segment tables
and retained episode reasoning; [LIBERO predictions](libero_predictions.md) preserve
historical integration results. Both Markdown files are **derived from native
JSON generations**, not human annotations or fresh model calls.

## What is included

| Path | Content / scope |
| --- | --- |
| `oopsie_dense_3529899/` | Original dense output, the exact run's jobs file, invocation/package/hash receipt and structural validation. |
| `oopsie_rubric_3529640/` | Original one-sample rubric output including native reasoning, run receipt and validation. |
| `oopsie_original_inputs/` | Original label-blind selection, provenance, dense and rubric jobs. The run-matching dense jobs bytes are in `oopsie_dense_3529899/jobs.jsonl`; that copy includes an extra trailing blank line relative to the local preparation copy here, with equal parsed rows. |
| `ten_corrected_inputs/` | Ten-episode selection including technical exclusions, corrected camera provenance and both label-blind jobs files. No completed ten-episode predictions exist at this snapshot. |
| `reference_three/` | Passed CPU media/default/postprocessing audit, pinned code hashes, original submission, viewer warning validation. GPU job 3530163 subsequently failed. |
| `reference_ten/` | Original ten-episode submission, staged payload hashes and passed native CPU media/defaults audit. GPU job 3530286 subsequently cancelled before starting. |
| `cuda_repair/` | Replacement submission and successful CPU compile-only receipt; GPU sampling remains unverified. |
| `video_export_manifests/` | Original O001–O003 annotated-video receipts: output/source hashes and per-frame display/timestamp checks. MP4s stay local. |
| `libero_dense_3528860/`, `libero_audit/` | Historical 12-episode native dense outputs, jobs, run/validation and exact reconstruction/weight audit. No new simulation labeling is proposed. |
| `scheduler_snapshot.txt` | Dated read-only scheduler observation, not a live display. |
| `artifact_manifest.json` | Internal source paths, byte lengths and SHA-256 of the 34 byte-preserved original files. |

Native output files and receipts were copied byte-for-byte. Existing absolute
paths in them describe the original machines; their videos are not bundled.
The current report supersedes historical status words inside older receipts.
Source videos/HDF5, model weights, environments, credentials and source outcome
annotations are excluded. Obtain dataset access and use the recorded pinned
release to rebuild playback locally; the [runbook](../../../flora_tacc.md) explains
the viewer and annotated-video commands. Rendering checks do not validate labels.

## Rebuild the readable results

From the repository root, with Python 3.12+ (no GPU or model needed):

```bash
E=docs/experiments/flora/2026-10-26
python scripts/tacc/summarize_flora_results.py \
  --dense "$E/oopsie_dense_3529899/dense.jsonl" \
  --dense-jobs "$E/oopsie_dense_3529899/jobs.jsonl" \
  --rubric "$E/oopsie_rubric_3529640/rubric.jsonl" \
  --rubric-jobs "$E/oopsie_original_inputs/rubric_jobs.jsonl" \
  --out outputs/flora_oopsie_predictions_rebuilt.md
python scripts/tacc/summarize_flora_results.py \
  --dense "$E/libero_dense_3528860/dense.jsonl" \
  --dense-jobs "$E/libero_dense_3528860/jobs.jsonl" \
  --out outputs/flora_libero_predictions_rebuilt.md
```

Use fresh output names. The renderer rechecks structural completeness and
recorded rubric sample count, preserves native boundaries/rationales, and prints
source hashes. It does not run inference or certify human correctness. Native raw
clip answers remain available in the preserved dense artifacts for stitching review.
