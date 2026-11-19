# Astra rich V8.2 labels: 1,000 OopsieData episodes

This versioned ZIP contains the completed labels from
`corral_astra_rich_failure_v8_2_carryforward_batch_v3`. All 1,000 dataset rows
record `gpt-6-astra`, verified against the native responses. Two rows are marked
human verified; schema validation does not establish label correctness.

The archive includes native Markdown annotations and responses, intermediate
carry-forward outputs, episode/source mappings, prompt and recipe snapshots,
the review page, and its Python server. Original videos, native HDF5 files,
model-input images, and frozen API requests are excluded. The video player
requires the separate original videos; the Markdown labels work independently.

After cloning or pulling this repository on your Mac, run from the repository root:

```sh
cd datasets/astra_v8_2_1000_v1
shasum -a 256 -c SHA256SUMS
unzip oopsiedata-astra-v8.2-1000-labels.zip
```

Open `oopsiedata-astra-v8.2-1000/report.md` for the label index. Individual labels
are in `oopsiedata-astra-v8.2-1000/canonical/C0001_final/annotation.md`, etc.
`dataset.jsonl` contains all 1,000 assistant targets, and `EXPORT_MANIFEST.json`
records checksums for the exported source artifacts.

The ZIP preserves original artifact bytes. Treat this directory as an immutable
dataset version; publish future label changes under a new version.
