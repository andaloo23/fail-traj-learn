# V9.1 twelve-episode pilot and conditional distillation plan

## Sol pilot approved for distillation experiments, 2026-10-27

The user said "all 12 sol annotations look good. lets move on." The Sol pilot
review gate has passed. The next stage is a label-only Qwen baseline followed by
controlled supervision and review-loop comparisons, described in
[the binary distillation experiment plan](oopsie_binary_distillation_experiments.md).
This records the episode-level approval without inventing individual browser
review notes or separate adjudications for every repeat. Native outputs and
frozen pilot split metadata remain unchanged. These reviewed recordings are now
training/debugging material, not a fresh final evaluation set. Bulk collection
and student training have not yet started.

## Completed, 2026-10-27

The user requested continuation after the credit stop. The original unanswered
credit-rejection attempt was archived under the run's `stopped_attempts/` with its
hash retained in `resume_*.json` and a readable `resume_*.md` note. The four
completed responses, frozen prompt/inputs/requests and $48 run-total ceiling are
unchanged. All **72/72 responses** subsequently completed and passed the binary
Markdown structural checks: O001–O012, both teachers, three repeats each.
Estimated generation cost is **$17.400060** at the frozen rates. Sol/Astra
frame-weighted agreement is **95.35%**, mean episode/pair agreement is **97.59%**,
and pooled failure IoU is **0.832**. These measure teacher agreement, not
human-reference accuracy. Episodes with any proposed failure are O003, O004,
O005, O008, O009, O011 and O012; individual repeats and boundaries require review.

Final preservation checks passed for the original four responses, frozen inputs
and requests, and the archived credit rejection. Browser checks passed 171 video
positions and 1,026 label/playhead checks across all twelve episodes, including
next-frame updates, with no JavaScript errors. Review all repeats at
`http://127.0.0.1:8797/review.html`; local `report.md`, `presentation_controls.md`
and `resume_completion.md` contain the results and verification record. The final
check helper's filename-selection bug was corrected; it did not affect generation
or native labels. Bulk collection and student training remain unstarted.

The shared binary reviewer shows labels by default for **every episode**,
including development/test recordings. Use the ordinary URL:
`http://127.0.0.1:8797/review.html`. Label visibility is one persistent viewer
setting; changing episodes or reloading does not reset it based on the split.
An explicit Hide labels (blind review) / Show labels for all episodes control
applies to the entire run. Notes continue to record actual teacher exposure.

The same fix is published to the older V9 and V9.1 binary reviewers. No episode
parameter or special link is required. The response count remains visible, label
data refreshes every 10 seconds while preserving the frame/repeats/notes, and UI
updates trigger a state-preserving reload. Review HTML is served without browser
caching, and complete page/data snapshots are published atomically.

### Regression checks for reviewer changes

Run both checks whenever changing the shared reviewer or its server. The browser
check must visit **every episode and repeat** across the available splits on a
plain URL, then verify visibility through navigation/reload, optional blind mode,
live label refresh, UI-version reload, frame stepping and HTML cache behavior.
It uses isolated browser storage and never saves human review notes or changes
native annotations.

```powershell
.venv-oopsie-distill/Scripts/python.exe -m unittest discover -s scripts/distill -p test_binary_segments_v9.py
.venv-review/Scripts/python.exe scripts/distill/check_binary_review_browser.py --url http://127.0.0.1:8797/review.html --browser "C:/Program Files/Google/Chrome/Application/chrome.exe"
```

The shared browser checker accepts other run URLs and Chromium executables. The
current twelve-episode check covers all 72 native responses, 171 video positions
and 1,026 label/playhead comparisons, plus mode/reload/refresh regressions. The
native request/output preservation audit covers 576 files across binary runs.

## Previous credit stop, 2026-10-26

All twelve inputs passed preparation and all 24 exact teacher requests passed
token/payload preflight. **Generation stopped after 4/72 accepted responses**:
O001 and O002 each completed Sol/Astra repeat 1, then O003 Sol repeat 1 received
HTTP 429 `credit_balance_exhausted`. No O003 model response was returned. The
collector stopped without retrying; remaining calls require restored API credits.
The run-total ceiling is $48 (conservative preflight estimate $47.062575), and
completed calls total an estimated $0.900457 at the recorded rates.

The partial reviewer is `http://127.0.0.1:8797/review.html`. All twelve original
videos are available there; the two completed episode pairs show native labels,
while other episodes clearly lack validated responses. Both completed pairs are
all-non-failure and agree 100%; this does not test positive failure recognition
or establish twelve-episode quality. Bulk labeling and training have not started.

All 1,353 original camera-frame JPEGs for the five old control episodes match
their prior V9.1 hashes. Sampled first/middle/last strips passed all 81 camera-panel
pixel comparisons. Thirteen offline tests passed; browser checks passed playback
and seeking at 36 positions across all twelve episodes, 12 available label checks,
and next-frame updates without JavaScript errors. These checks validate input
and display fidelity, not model correctness.

## Protocol

This run extends binary failure segmentation to **O001–O012**, using real
OopsieData release `da4b16512b77f7324296a66da7c0067a40539895`. The prompt remains
the frozen `scripts/annotate/prompts/binary_failure_v9_1.md`. It returns native
Markdown containing start frame, end frame and Failure Yes/No, without categories
or explanations. Original five-episode V9.1 requests and outputs stay unchanged.

Configuration: `configs/oopsie_binary_v9_1_twelve_v1.json`; output:
`outputs/oopsie_binary_v9_1_twelve_v1/`. Both original teachers (Sol/Astra), low
reasoning and three independent repeats are retained: **72 planned generation
calls**. These are fresh calls, not copies of the five-episode labels.

## Data and image presentation

O001–O010 keep their original real recording identities and lab split metadata.
O011 is `labs/Berkeley_RAIL/09bb143989db.h5`; O012 is
`labs/Enatic_OpenArm/101.h5`. The two additions are the first other manifest
recordings with 80–250 frames in these labs, chosen without consulting source
outcome labels. Source HDF5/video hashes, decoded clocks, frame counts and camera
views were checked. First/middle/last camera sheets are saved under
`outputs/oopsie_binary_twelve_setup_v1/`. This is a diagnostic sample, not a
representative or failure-balanced benchmark.

The existing ten recordings include five with more than 1,500 individual camera
images at native rate. The API allows up to
[1,500 images and a 512 MB payload per request](https://developers.openai.com/api/docs/guides/images-vision).
The new presentation therefore packs synchronized camera views **side by side in
one image per original timestamp**. It preserves every frame, all selected views,
their order and the existing maximum 280 px side per camera. Panels retain their
pixels and are packed losslessly into PNG after the ordinary JPEG frame export;
black padding is described explicitly. No temporal sampling or windowing is used.
The largest episode supplies 1,200 images, each potentially containing multiple
cameras. Original camera JPGs are retained in `source_images` for auditing.

The user prompt is unchanged; an input-format note describes panel order. This
is a separately versioned **presentation change**, so comparisons to old V9.1
cannot be attributed solely to new recordings. The five previously labeled
episodes are rerun as presentation controls. Encoded timing checks do not prove
physical capture synchronization.

Longer inputs require a higher local token ceiling (600,000 versus 80,000).
Official model pages document 1,050,000 context for
[Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) and
[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra). A complete
input-token preflight checks every exact frozen request before generation.
Requests over 272,000 input tokens use the documented 2x input/cache and 1.5x
output price multipliers. These are estimates at recorded rates, not invoices.

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py prepare --config configs/oopsie_binary_v9_1_twelve_v1.json
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py preflight --run outputs/oopsie_binary_v9_1_twelve_v1
# Select the run-total dollar ceiling from the preflight receipt.
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py collect --run outputs/oopsie_binary_v9_1_twelve_v1 --budget-usd RUN_TOTAL_CEILING
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py report --run outputs/oopsie_binary_v9_1_twelve_v1
.venv-oopsie-distill/Scripts/python.exe scripts/distill/binary_segments_v9.py review --run outputs/oopsie_binary_v9_1_twelve_v1
```

Preparation requires a fresh versioned directory. An unfinished or structurally
invalid generation stops the collector and is preserved rather than repaired or
resent. Preflight token counts are reused only when manifest/request hashes still
match. No bulk collection or training is authorized by passing structural checks.

## What to review before scaling

Watch all twelve original episodes with native Markdown overlays side by side,
including every repeat. Check clear failure events and recoveries, clean negative
spans, onset/offset placement and the longer multiview episodes. Inspect the
five presentation controls against their prior V9.1 labels. Save human decisions
in Markdown; teacher agreement alone does not establish accuracy.

`report.md` includes percentage frame agreement, within-teacher repeatability,
frame-weighted and mean-episode Sol/Astra agreement, failure IoU and the episodes
with any proposed positive interval. All-negative pairs have undefined failure
IoU, not a perfect failure score. Repeats are not independent evaluation episodes.

## Conditional 500-episode collection and training

The user has approved the Sol pilot for moving to distillation experiments.
The original provisional
interpretation is **500 total episodes: 450 training and 50 validation**, pending
the user's choice of whether they instead mean 500 training plus 50 validation.
No 500-episode collection, Batch submission or student training starts in this
pilot step.

Before collecting at scale:

1. Freeze the binary definition, prompt, camera presentation and teacher-target
   policy. Decide which teacher supplies training targets and how disagreements
   are reviewed; do not choose targets from validation performance.
2. Freeze an episode-disjoint split before labeling/training. Keep all reviewed
   pilot recordings and their source duplicates out of the final 50. Group
   related recordings/sessions to limit near-duplicate leakage; preserve task/lab
   provenance and disclose whether validation measures within-lab or held-out-lab
   transfer. The pilot's earlier `test` flags do not make its now-inspected videos
   a fresh final validation set.
3. Check duration, camera count, image/payload limits, teacher context and cost
   over the selected corpus. Do not silently drop frames from long recordings.
   If a different packing or window protocol is needed, validate it in a new
   version before collection. API Batch cost/format and teacher availability must
   be verified when actually submitting the bulk job.
4. Freeze the validation labels and review a positive-containing subset against
   original videos. Do not manufacture failures or select the entire validation
   set based on the evaluated model's predictions. Report any intentionally
   balanced diagnostic subset separately from the main validation distribution.
5. Add a **binary Markdown** SFT/export/evaluation path for the student. Existing
   rich-schema SFT code is not automatically compatible with this three-column
   target. Check the student's context budget on the actual evidence; whole-rate
   teacher inputs do not imply they fit the smaller student. Keep all windows of
   one source episode in the same split if a reviewed window adapter is used.

The requested primary metric is **student–teacher frame agreement percentage**:
expand each half-open Yes/No interval to the original source frame grid and count
matching labels once per frame, not once per camera. Report both pooled
frame-weighted agreement and the mean of 50 per-episode agreements. Use fresh
student predictions and frozen teacher references with the same task definition.

Also report failure precision/recall/F1, failure IoU, per-episode positive-frame
counts, structural failure rate and an all-non-failure baseline. Count an invalid
prediction explicitly; never turn it into a negative timeline. If ambiguous human
spans are masked, report their count and evaluated coverage. Teacher agreement
measures imitation; human-reviewed references are required for a claim of actual
failure-recognition accuracy. Use an additional untouched test set if the 50
validation episodes are used repeatedly for model or prompt selection.
