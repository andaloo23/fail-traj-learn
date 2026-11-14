# Fresh Corral sample and Astra rich failure pilot

Status on 2026-11-12: the user reauthenticated TACC. The 1,000-episode sample is
frozen, collected from Corral, and all source checksums match. All 10 pilot episodes
are prepared. Portkey rejected token preflight with HTTP 401, Invalid API Key;
the user has been asked to update `.env.portkey`. No model generation has been
submitted. Runtime details are in the run's `sample.md` and preserved receipts.

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
