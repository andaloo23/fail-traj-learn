# Complete the frozen 1,000 episodes with all-frame Batch calls

The user reviewed C0052 and C0188, then explicitly approved finishing labeling
with the reviewed sequential technique, Batch mode to minimize cost, and every
recorded frame. The later every-other-frame idea was explicitly withdrawn.

The run is
`outputs/corral_astra_rich_failure_v8_2_carryforward_batch_v3`. Its worker is
`scripts/distill/corral_astra_carryforward_batch.py`. The original bulk run,
pilot runs, frozen requests/responses, and human-review artifacts remain intact.

The run reuses 936 validated original native targets and both reviewed pilot
reconciliations: 938 labels without new generation. It labels only the remaining
62 original episodes, including C0242 whose earlier response failed validation.
Every distinct camera view and recorded video frame is retained at the reviewed
preparation dimensions. New annotation intervals are disjoint 350-frame parts;
each later part receives exactly the two preceding source frames and its validated
predecessor's complete native Markdown annotation. Source indices/timestamps stay
global. The deterministic recipe plans 479 new part calls and 62 reconciliations.

All new generation targets `gpt-6-astra` through Portkey and the Batch API. There
is no synchronous generation fallback. Independent episodes run concurrently;
each episode advances only after its previous result is collected and validated.
Different episode chains can advance at different rates without waiting for a
global barrier. Each batch has a 24-hour completion window, so chronological
dependencies can extend overall turnaround beyond one batch window.

Cache breakpoints cover only the common prompt text. Episode metadata, previous
annotations, and unique images follow the breakpoint and do not incur explicit
cache writes. Input preflights enforce 1,500 images and a conservative 240,000
input-token ceiling per request, below Astra's higher long-input pricing tier.
Oversized transport uses separately frozen uploaded-image references with exact
source-pixel provenance. New Batch files stay below 185 MB and active queued
input stays below 2.5 million tokens.

Submission journals are written before generation submission. An unknown Batch
creation outcome is never automatically resent. Immutable file staging can retry
safely before generation begins. A completed malformed answer or a known terminal
transient Batch failure can receive at most two explicitly recorded repair
attempts, each still in Batch mode and inside the original episode scope. Native
failed outputs remain preserved. Actual returned model identity is retained.

The initial cost projection is approximately **$132.63 additional**, or **$358.03
total**, including $225.40 in previously recorded usage from the original run and
both pilots. This projects image inputs from actual prepared dimensions and frame
counts and uses pilot average output/reconciliation sizes. It assumes no cache-hit
credit and includes a shared-prefix write allowance. Future predecessor text and
output lengths remain variable. Historical pilot gateway-error charges were not
returned with usage and remain unverified; they are excluded. The $250 additional
budget guard is a safety ceiling rather than an expected expenditure.

The worker preserves native Markdown targets, exports the growing 1,000-episode
dataset with provenance, and publishes video playback and aligned annotations at
`http://127.0.0.1:8814/review.html`. Runtime `report.md` gives readable progress and
cost. Internal `queue_status.json`, immutable native responses, and Batch receipts
provide detailed operational evidence. No distillation/training is launched.

```powershell
.venv-oopsie-distill/Scripts/python.exe -m unittest discover -s scripts/distill -p 'test_corral_astra*.py' -q
.venv-oopsie-distill/Scripts/python.exe scripts/distill/corral_astra_carryforward_batch.py init
.venv-oopsie-distill/Scripts/python.exe scripts/distill/corral_astra_carryforward_batch.py run
```

Use `run` only after initialization; never initialize a replacement over a frozen
run. An active worker owns `worker.lock`. To request a cooperative stop, create
`STOP_REQUESTED.json` in this run. Inspect unknown submissions before restarting;
do not delete journals to force a resend. Reversible local preparation and safe
file staging do not establish that a model-generation request was submitted.
