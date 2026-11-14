# Additional 500-video Sol collection

The user authorized another 500 real OopsieData videos using the previous
collection's Sol prompt, Batch API, and preparation method, operated on the local
PC. The previous frozen collection remains unchanged. No TACC jobs or student
training are part of this collection.

- Run: `outputs/oopsie_rich_failure_v8_1_additional_500_batch_v2/`.
- Unchanged real-data release, V8.1 prompt, `gpt-6.1-sol`, low reasoning,
  one request per episode, and native Markdown outputs.
- Same 400 training / 50 development / 50 test split and held-out labs.
  Combined with the original collection this targets 800 / 100 / 100 videos.
- All recorded frames and distinct camera views retained, with the same
  280-pixel camera preprocessing and lossless synchronized strips.
- Same actual-token preflight, 8,192-token output allowance, cache-write and
  long-context reserves, and **$75 maximum generation budget**.
- The existing direct OpenAI Batch API credential and transport are reused;
  this collection does not change to GPT-4o or Portkey.

The seeded candidate IDs and reserve order are retained from the original
selection procedure. Previously selected release paths, HDF5 hashes, exact
multicamera video sets, and episode IDs are excluded before preparation.
Previously documented technical exclusions are also skipped. No source outcome
labels or teacher labels are used to select new episodes. The new frozen plan
records hashes of the prior selection and configuration.

Local preparation uses four CPU workers and token preflight uses two workers.
The existing queue waits for all 500 inputs to be frozen and for the total
preflight ceiling to fit the budget before buying annotations. It keeps the
same remote token cap, submission journals, collection, validation, and refusal
to automatically retry failed or uncertain generations.

Run `scripts/distill/launch_additional_oopsie_batch_v2.py` with the existing
`.venv-oopsie-distill` Python environment. It supervises preparation, preflight,
Batch collection, and the status monitor, and starts video review at
<http://127.0.0.1:8801/review.html>. This URL becomes available after the review
page is published. The existing viewer and training queue are left in place.
Do not start duplicate workers if a batch is slow. Read `status.md`,
`local_controller_status.json`, and the preserved submission journals instead.

The local PC downloads and prepares evidence, submits requests, and collects
results. Sol inference executes remotely through the API; it does not consume
the local training GPU. The ordinary video reviewer receives the same full
browser regression after collection. Previously invalid annotations are not
silently repaired or replaced by this expansion.
