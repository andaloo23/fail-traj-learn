# Input reduction for progress/failure annotation

Historical unrun proposal. Superseded by the
[controlled frame-selection design](frame_selection_experiment.md), which adds
separate Gemini selection and GPT annotation prompts with matched controls.
The runner described below implements this older independent-only matrix; it must
not be run as a substitute for the new design. This older matrix remains unrun;
the user authorized the replacement frame-selection experiment.

Question: can visual input be reduced without materially degrading the usefulness
of progress/failure annotations for a human reviewer? This is a small screening
experiment, not evidence of statistical equivalence or non-inferiority.

## Paired conditions

Use the first four IDs in the existing development review pack: R001 tomato sauce,
R002 butter, R003 orange juice, R004 milk; all tasks are pick-and-place into a basket.
No outcome or prior label was consulted for selection. These are development data,
not independent held-out cases or a representative sample of robot failures.

| Arm | Visual input | Models | Calls |
|---|---|---|---:|
| baseline | Individual 256x256 images from both cameras at 4 FPS, plus final frame | GPT and Gemini independently | 8 |
| sparse | Same at 1 FPS, plus final frame | GPT and Gemini independently | 8 |
| small | Same 4 FPS timestamps, each camera resized to 128x128 | GPT and Gemini independently | 8 |
| video | Separate synchronized 256x256 videos for both cameras; request 4 FPS sampling | Gemini alone | 4 |

Twenty-eight generation requests total. Gemini never sees GPT output and GPT never
sees Gemini output. A whole episode goes into each independent request; no chunks
with carried conversation, model-to-model review, examples, or multi-stage chain.
One run per cell measures feasibility and candidate differences, not stability.

All arms receive identical task text, common instructions, Markdown output guidance and ordinary
telemetry sampled at 4 FPS plus the last frame. Telemetry is separate from camera
captions so reducing the image rate does not also remove robot measurements.
Keep model reasoning low, output budget 4,096 tokens, camera count, JPEG quality,
and category definitions fixed. The representation/timing description changes by
arm so the model knows what it was shown; it is not told an arm is expected to win.

The `small` arm tests resolution, not necessarily billing reduction. Providers may
assign the same tokens to differently sized small images; measure token usage.
Native video changes provider decoding and temporal encoding, and its actual sampled
frames are not exposed. It is an exploratory delivery-method comparison, not a
pixel-identical controlled ablation. Native videos preserve the original 20 FPS
timebase and use H.264 CRF 18 / yuv420p compression; request sampling is explicitly
4 FPS. Compression is part of this exploratory representation comparison.

Four FPS is a pragmatic baseline, not established sufficient evidence. We cannot
claim preservation relative to full-frame annotation. For human review, inspect
the full original 20 FPS recordings, especially brief interactions and boundaries.

## Prompt and outputs

Exact common prompt: `outputs/api_input_ablation_v3/prompt.md`.
Per-request context adds ID, task, source FPS/length, shared telemetry, visual
sampling/resolution, and ordered image pairs or native videos. No private simulator
state, terminal outcome, annotation candidates or reference scores are transmitted.

Output intervals have progress/failure labels, allowed failure categories,
descriptions, evidence frames and uncertainty. Progress and failure may overlap.
No neutral/recovery labels, severity, resetability or recovery advice. Missing labels
remain unknown. All arms may estimate boundaries on the same source-frame grid;
image evidence indices must refer to an actually supplied frame. This separates
sampling uncertainty from an artificially coarser output format.

The canonical prompt is `scripts/annotate/prompts/progress_failure.md`; preparation
copies it into the frozen pack. Each arm has a `context.md` containing episode
metadata and a Markdown telemetry table. Both providers receive these as ordinary
text. JSON output mode is disabled. Candidate annotations are saved verbatim as
`<episode>_<arm>_<provider>_annotation.md`. Only a minimal nonempty/unfenced-text
check is automatic; boundaries, labels and evidence require human review. API
transport envelopes, raw provider responses, manifests and usage ledgers remain
JSON internally; the model is not asked to produce those files.

## Review and subsequent experiments

Create independent human labels from full recordings before showing predictions
where feasible. Review candidate differences in shuffled/blinded order. Record:

- omitted or invented progress/failure intervals;
- incorrect target identity or failure category;
- boundary differences and whether the evidence resolves them;
- unsupported explanations, uncertainty, and amount of human correction;
- reviewer time, actual input/output/thinking tokens, latency and estimated cost.

Do not score against the withdrawn simulator-derived reference, equate agreement
with correctness, or use the richer-input model as ground truth. Agree on acceptable
error/boundary tolerances with reviewers before choosing a winning condition.
An omission on a consequential failure should not be hidden by an aggregate score.

After this screen, repeat baseline and a promising cheaper condition on fresh
human-reviewed episodes before claiming quality is preserved. Do not tune on those
confirmation labels. Contact sheets, lower provider media-token settings, one-camera
input, adaptive frame selection, and coarse-to-fine calls are separate later arms;
mixing them into this first screen would make attribution and spending harder.

## Cost and execution control

Generation is blocked above **40,000 provider-counted input tokens**. Each request
sets **4,096 total output tokens, including reasoning/thinking**. At reviewed standard
prices, even allowing input billing twice (preflight and generation):

- OpenAI: 2 * 40,000 * $2 / million + 4,096 * $10 / million = $0.20096;
  reserve $0.22 per attempt, 12 attempts = **$2.64**.
- Gemini: 2 * 40,000 * $1 / million + 4,096 * $5 / million = $0.10048;
  reserve $0.12 per attempt, 16 attempts = **$1.92**.

Total reserved maximum: **$4.56**, below a $5 experiment allowance. No caching discount
assumed. Token preflights generate no annotations. Prices reviewed 2026-10-01;
runner expires after 2026-12-31. This controls this runner, not unrelated account use.
Each attempt is reserved before network access. Stop on any count, HTTP, timeout,
truncation or basic output-format error. No retry, repair or expansion. A persistent run lock
and exclusive attempt files prevent accidental reruns. Failed calls keep their
reservation. A stopped matrix remains incomplete pending a separately approved fix.

Sources:
[OpenAI pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
[OpenAI output-token limit](https://developers.openai.com/api/docs/guides/token-counting),
[Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing),
[Gemini combined thinking/output limit](https://ai.google.dev/gemini-api/docs/generate-content/thinking),
[Gemini video sampling](https://ai.google.dev/gemini-api/docs/generate-content/video-understanding).

## Offline preparation

Requires NumPy, Pillow, and imageio-ffmpeg in the existing review environment.
FFmpeg is used locally to encode videos; preparation and inspection do not call APIs.

```powershell
.\.venv-review\Scripts\python.exe scripts/annotate/api_input_ablation.py prepare
.\.venv-review\Scripts\python.exe scripts/annotate/api_input_ablation.py inspect
.\.venv-review\Scripts\python.exe -m unittest discover -s scripts/annotate -p test_api_input_ablation.py -v
```

Review `outputs/api_input_ablation_v3/index.html`, `prompt.md` and `manifest.json`.
The freeze records all model-visible artifacts, source hashes and both runner modules.
After user approval of the final plan, execute only the approved manifest:

```powershell
.\.venv-review\Scripts\python.exe scripts/annotate/api_input_ablation.py run --approve-manifest-sha256 <approved-hash>
```

Credentials come from the existing `.env` (OpenAI first, Gemini second). Raw responses,
candidate Markdown files and usage records are saved separately from source labels.
On completion, `results.html` presents the candidates for human review.
