# Portable Astra labels

1000 real OopsieData episodes with rich V8.2 Markdown labels.
Native teacher identity is preserved in dataset.jsonl and canonical/*/response.json.
Only 2 dataset rows are marked human_verified; schema validation is not human adjudication.

Read report.md for the episode index and canonical/C0001_final/annotation.md for an example.
dataset.jsonl contains the assistant targets. catalog.json and selection.json map labels to source episodes and cameras.
The canonical folder includes final native outputs and intermediate carry-forward outputs.
Prompt and recipe snapshots are included. This is a portable label/review export, not a full frozen-request or training-data archive.
Original collection artifacts remain on the source computer. Model-input images and native HDF5 files are excluded.

## On your Mac

Extract oopsiedata-astra-v8.2-1000-labels.zip. If you also have oopsiedata-astra-v8.2-1000-videos.tar,
extract both archives into the same parent directory. They share the oopsiedata-astra-v8.2-1000/ folder.

```sh
unzip oopsiedata-astra-v8.2-1000-labels.zip
tar -xf oopsiedata-astra-v8.2-1000-videos.tar  # Only when transferring videos too
cd oopsiedata-astra-v8.2-1000
python3 scripts/distill/serve_oopsie_review.py --directory . --port 8814
```

Open http://127.0.0.1:8814/review.html for video playback and time-aligned labels.
Video playback requires the separate videos archive. Reading Markdown labels requires no server.
The server supports seeking and saves new Markdown notes under reviews/.

Verify transferred archives from their parent directory with:

```sh
shasum -a 256 -c SHA256SUMS
```

EXPORT_MANIFEST.json records SHA-256 checksums of exported files and original videos.
Historical provenance may mention source-computer paths; review media and native responses use relative paths.
