# Fresh Corral sample and Astra rich failure pilot

Status on 2026-11-14: the replacement Portkey key authenticated and all ten
prepared Astra pilot requests completed using the frozen rich V8.2 prompt. Every
native response records `gpt-6-astra` and passed schema validation. Browser checks
on the actual pilot passed all ten episodes, 44 frame positions and 50 judgment
field checks with zero JavaScript errors. Recorded-usage inference estimate: $4.18
at checked public rates; label correctness awaits human review. The 1,000-episode
Corral sample remains frozen and checksum verified. The approved full-dataset
Batch expansion is running as documented below. Pilot review is at
`http://127.0.0.1:8808/review.html`; full-run progress is at
`http://127.0.0.1:8809/review.html`. Runtime details are in each run's `report.md`
and preserved receipts. Historical authentication failures remain preserved.

Verified source: `/corral/utexas/IRI26024/oopsiedata/OopsieData-Submissions/oopsiedata-v0.1`.
Its episode inventory checksum matches the local released corpus exactly, with
10,677 eligible episodes. Seed: `7790449694665858644`. There are no technical or
previous-run exclusions. The sample includes 21 `.hdf5` episodes and four episodes
with release-corrected video references, as well as ordinary `.h5` episodes.

## Authorized scope

- Uniform random sample of 1,000 real OopsieData episodes on TACC Corral, without
  replacement. No exclusions based on previous datasets, teacher outputs, source
  outcomes, lab balancing, duration or camera count. Invalid release metadata is
  documented separately. Check Corral membership before freezing the selection.
- Collect selected native HDF5s and referenced original videos from Corral, verify
  every file against the pinned real OopsieData release checksums, and retain an
  internal provenance manifest. A local inventory is available for release
  `da4b16512b77f7324296a66da7c0067a40539895`; verify its layout and coverage against
  the actual Corral dataset before using it. Do not silently substitute Hugging
  Face downloads or a previously selected sample for the requested Corral source.
- Label only the first 10 episodes in the frozen random ordering: one GPT-6 Astra
  response per episode through Portkey, low reasoning effort, native Markdown,
  12,000 maximum output tokens, no client generation retries. The remaining 990
  episodes await the user's review. No training or cluster jobs are authorized by
  this labeling request.
- Provide original video playback with time-aligned failure annotations and
  Markdown human review notes. Preserve prior runs and their review notes.

## Prompt lineage and schema

The user confirmed using the rich V8 lineage. The new prompt is
[`rich_failure_v8_2.md`](../scripts/annotate/prompts/rich_failure_v8_2.md), based on
V8.1's evidence-based failure recognition, categories and explanations. V8.1 itself
incorporated V9.1 recognition rules; V9.1 is the separate binary-only prompt.
The older V10-V15 taxonomy experiments belong to another version series.

V8.2 adds the attempted language task, the four requested episode outcome labels,
separate recovery advice, severity with supporting observations, and resetability
with an explanation of the intervention required. The exact output values are:

| Field | Values |
| --- | --- |
| Success label | success; failure; success but suboptimal; success but side effects |
| Severity | low; medium; catastrophic |
| Resetability | immediate; minor_reset; hard_reset; unresettable |

The prompt includes the user's full definitions and examples. Severity describes
consequences and supported risk; resetability describes restoring the environment.
They are separate judgments. Recovery advice is a suggestion, not an observed event.
Following the user's segment instructions, distinct consecutive failure types can
have separate segments. Adjacent No intervals merge. This intentionally extends
V8.1's binary-boundary merge rule in this new version; frozen V8.1 outputs stay intact.

Every frame is covered by a Yes/No timeline; each Yes row has one matching failure
annotation. Explanations and episode outcome evidence cite supplied source frames
and native cameras. A video ending alone does not establish abnormal termination.
Unconfirmed episode completion is distinguished from a visibly failed attempt;
missing success evidence alone does not create a local failure segment.

## Resume after authentication

From WSL, authenticate interactively; enter credentials at the terminal prompts:

```bash
cd /mnt/c/Users/LocalPC/dev/fail-traj-learn
bash scripts/tacc/connect_tacc.sh al62479 login2.ls6.tacc.utexas.edu
```

The release directory containing `labs/` has now been verified at the source path
above. Corral also contains separate raw lab submissions and tooling repositories;
the sampling population is the complete consolidated OopsieData v0.1.1 release.

The prepared runner is `scripts/distill/corral_astra_v8_2.py`. Its commands are
`plan`, `fetch`, `prepare`, `preflight`, `label`, and `review`. `plan` requires
`--corral-release-root`; it records a fresh random seed, source inventory hashes,
the selected order, all source references and the pilot IDs in a new run.
The default run is `outputs/corral_astra_rich_failure_v8_2_1000_v1`.

`fetch` streams only selected source files from Corral into a flat content-addressed
cache and verifies checksums. `prepare` can run after the ten pilot episodes have
arrived while the remaining source files are still transferring; labeling requires
the entire 1,000-episode collection to pass verification. It retains all
recorded frames and distinct camera views, and uses V8.1 preprocessing (280-pixel
maximum side per camera, JPEG95 pixels in lossless camera strips). A technical
failure stops preparation without outcome-driven pilot substitution. C0007 has
241 video observations in all three cameras versus 240 robot timesteps: the
visual-only annotation retains all 241 frames and records both counts. The initial
state-count preparation rejection is preserved in `preparation_attempts/`.
No source annotations enter model requests.

`preflight` freezes the exact requests and counts their input tokens through
Portkey. It rejects context overflow rather than truncating. Astra's checked
[model documentation](https://developers.openai.com/api/docs/models/gpt-6-astra)
supports the Responses endpoint and image inputs. The recorded conservative
generation ceiling includes possible cache writes and long-context multipliers;
it excludes separate Portkey fees. `label --budget-usd AMOUNT` enforces that ceiling
and the fixed 10-episode pilot. Choose the pilot budget after the actual preflight;
the request already authorizes these 10 labels, so no second approval is needed
within that scope. Submission journals prevent silent resends after ambiguity.

`review` publishes a dedicated Astra viewer. Serve it with
`scripts/distill/serve_oopsie_review.py --directory RUN --port 8808`, then use
`http://127.0.0.1:8808/review.html`. Labels appear by default for every episode;
blind mode persists across navigation/reloads. The viewer shows episode outcome,
recovery, severity and resetability, plus native Markdown downloads and notes.

## Verification completed before source access

- Seven unit tests passed for schema boundaries, required fields, taxonomy/enum
  rejection, supplied frame/camera evidence, distinct adjacent failure segments,
  the 10-episode cap, explicit Portkey-only configuration, and retention of an
  extra terminal video observation.
- The required shared binary browser checker passed against the ordinary URL of
  a **separate UI fixture**, covering all 10 fixture episodes/repeats, 35 video
  positions, navigation, reloads, live label arrivals, persistent visibility and
  frame stepping. A second browser check passed 50 visible recovery/severity/
  resetability field checks, including time-aligned cards and mobile overflow.
  Both recorded zero JavaScript errors.
- The fixture reuses original OopsieData media with fabricated annotation strings
  solely for browser checks. It is explicitly marked as a test fixture, not the
  requested random dataset or Astra output. No paid model calls were made.
- After the real pilot completes, run both browser checkers again against its
  ordinary URL before presenting it as ready for human review.
- Prelabel playback checks on the actual ten pilot episodes passed decoding and
  beginning/middle/end seeking in every camera (30 video positions), with zero
  JavaScript errors. These checks establish media operation, not label quality.

Receipts: `outputs/corral_astra_v8_2_ui_fixture_v1/binary_checks/browser_check.json`
and `outputs/corral_astra_v8_2_ui_fixture_v1/judgment_checks/severity_resetability_check.json`.

## Approved full-dataset expansion, 2026-11-14

After viewing the ten-episode pilot, the user approved generating the full frozen
1,000-episode dataset. The versioned expansion is
`outputs/corral_astra_rich_failure_v8_2_1000_batch_v2`, driven by
`scripts/distill/corral_astra_v8_2_batch.py`. The original selection, pilot prompt,
requests, native responses and human review notes remain preserved. The ten pilot
responses are reused with recorded source request/response hashes; only the other
990 episodes need new teacher responses. All labels retain actual native model
identity. This approval does not authorize training or another sample.

The rich V8.2 prompt text, low reasoning effort, 12,000-token output allowance,
per-camera JPEG95 preprocessing and 280-pixel maximum camera side are unchanged.
New requests use the Portkey Responses Batch endpoint with explicit-only caching:
the exact shared prompt ends at a cache breakpoint; changing episode metadata and
images follow it without cache writes. The first three new dataset episodes
successfully returned native `gpt-6-astra` Markdown. Actual usage confirmed a
1,912-token shared cache prefix, with no cache writes for episode images.

The operational ceiling is USD 800 in conservative committed Batch generation
cost. It assumes no cache hits and the full output allowance; it is a submission
guard, not an invoice. Queue occupancy is capped at 2.5 million input tokens.
Requests and batch files are frozen and hashed before submission. Batch creation
and model generation are never automatically resent after an uncertain outcome.
Token counting, read-only polling and immutable staging uploads may retry with
retained attempt records; staging retries reuse the same idempotency key and exact
file bytes. JSON request bodies above a conservative 75 MB transport threshold
use uploaded images referenced by file ID, targeting a 50 MB body. The threshold
is operational: requests up to 71 MB succeeded while bodies over 120 MB repeatedly
failed at the gateway. It is not a claimed provider specification. If provider
MIME detection rejects a valid WEBP, a lossless PNG staging copy is allowed only
after verifying identical decoded RGB bytes; both source and transport hashes
are retained. No frame is silently dropped, sampled or replaced.

Robot state counts and native video observations are retained separately. For
video-only annotation, camera-agreed counts differing by one observation from
robot states are supported. Nonuniform native presentation timestamps are retained
and supplied to the teacher and viewer rather than rejected against average FPS.
Earlier technical preparation attempts remain archived. This preserves all actual
video observations without inventing a missing observation.

Sixty-three episodes exceed the 1,500-image request limit in the reviewed per-frame
format; the user has been asked whether to package these as pixel-preserving
chronological contact sheets. They remain held pending that choice. Any episode
still above Astra's 922,000-input-token limit also remains held; no truncation or
silent multi-call synthesis is allowed. A pixel-verified packaging preview is in
the expansion's `packaging_preview/` directory.

Full-run review: `http://127.0.0.1:8809/review.html`. The established reviewer keeps
labels visible by default, persistent blind mode, original camera video playback,
source-frame stepping, per-segment severity/resetability and Markdown notes.
The native-timestamp viewer and shared browser checker support explicit frame
times, with the former FPS behavior as a fallback for historical runs. Browser
checks must be rerun on all available labels after collection stabilizes.

The runner exports currently validated native Markdown assistant targets inside an
operational `dataset.jsonl`, with request/response hashes and native teacher model
identity. `dataset_manifest.json` explicitly reports whether all 1,000 targets
are complete; neither schema checks nor successful export establishes human label
correctness. No training is launched.

Resume and inspect using the existing environment:

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/corral_astra_v8_2_batch.py run
.venv-oopsie-distill/Scripts/python.exe scripts/distill/corral_astra_v8_2_batch.py review
.venv-oopsie-distill/Scripts/python.exe scripts/distill/corral_astra_v8_2_batch.py repair-transport
.venv-oopsie-distill/Scripts/python.exe scripts/distill/corral_astra_v8_2_batch.py finalize-review
```

Check `queue_worker.lock` and its PID before resuming; an existing live worker
owns the queue. `queue_status.json`, `preparation_audit.json`, `dataset_manifest.json`
and the append-only native trace artifacts describe actual progress. An unresolved
batch submission journal requires inspection before any resend. Reviewable progress
is also in `report.md` and the ordinary viewer URL.

The transport repair helper only handles nongenerating staging/preflight failures;
the queue remains the sole batch-submission owner. The review finalizer waits for
runnable batch results to stabilize, checks the ordinary viewer across all 1,000
episodes and available repeats, and records both full browser and judgment-field
check results. Initial live checks covered playback readiness in all 1,000 episodes
and 70 judgment fields with zero JavaScript errors; an initial frame-seek check
timed out while preparation metadata was still changing. Full checks are therefore
pending stabilization, not reported as generally passing. Sixteen local tests
passed for schema, source clocks, exact-pixel transport, cache boundaries, cost
guards, frozen-request integrity, teacher identity and submission journals.
