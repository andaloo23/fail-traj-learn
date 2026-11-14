# Small progress/failure API annotation pilot

Status: unrun and superseded by [the input-reduction experiment](api_input_ablation.md).
No approval was granted for this original pilot; use the revised plan for review.

The pilot checks whether two models return reviewable progress/failure intervals,
what they disagree about, and actual token usage. It is a workflow development
experiment, not an accuracy benchmark or training experiment. There is no scoring
against simulator references. Human inspection is the next step.

## Exact scope

- R001: pick up the tomato sauce and place it in the basket; 280 frames at 20 Hz.
- R002: pick up the butter and place it in the basket; 150 frames at 20 Hz.
- These are the first two IDs in the existing development review pack. They are
  not new held-out episodes and are not claimed to represent particular outcomes.
- Each model receives one independent request per episode, with the same prompt,
  task text, sampled camera pairs and observable robot telemetry.
- Sample every fifth frame plus the final frame: 57 and 31 paired timestamps,
  respectively, with two native 256x256 JPEGs per timestamp. No outcome,
  simulator-contact state, reference labels, previous GPT labels or examples.
- Models: `gpt-6.1-sol` (Responses API, standard service, high image detail,
  low reasoning) and `gemini-robotics-er-2-preview` (generateContent, low thinking).
- At most four generation attempts, one per episode/model; one token-count
  preflight per attempt. No tools, repeats, repair calls, or automatic retries.
- Outputs: independent progress and failure intervals, potentially overlapping;
  failure taxonomy, descriptions, evidence frames and uncertainty. No neutral or
  recovery class. Unannotated regions never become verified negatives.

Four-Hz sampling can miss brief interactions and only supports coarse boundaries.
This pilot evaluates workflow feasibility; finer sampling is a separate experiment.

## Spending controls

The entire run reserves **$2 USD maximum: $1 OpenAI and $1 Gemini** at the reviewed
standard prices. This is a conservative runner allowance, not an account-wide
billing limit; unrelated API usage is outside it.

Before sending each token-count request, the runner persistently reserves $0.50
in an exclusive attempt file. A failed request, timeout or crash retains that
reservation. A persistent run lock prevents rerunning even after interruption.
No reservations are refunded or recycled. Do not delete the lock/ledger to retry.

Generation is blocked unless the provider reports at most 80,000 input tokens.
Each request sets a 4,096 output-token limit. The allowance is deliberately loose:

- OpenAI: even counting input twice at $2/million and 4,096 output tokens at
  $10/million gives $0.361 per attempt, below $0.50.
- Gemini: counting input twice at $1/million and conservatively allowing the
  model's entire 65,536-token output capacity at $5/million gives $0.488 per
  attempt, below $0.50. The actual request cap is much smaller.

The token-count endpoints do not generate annotations. If either preflight is
unavailable or rejects the payload, stop for inspection; do not bypass it.
No cached-input discount is assumed. Pricing must be re-reviewed after 2026-12-31.

Sources reviewed 2026-10-01:
[OpenAI model/pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
[OpenAI token counting](https://developers.openai.com/api/docs/guides/token-counting),
[Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing),
[Gemini model limits](https://ai.google.dev/gemini-api/docs/models/gemini-robotics-er-2-preview).

## Prepare and inspect offline

From the repository root, using the existing review environment:

```powershell
.\.venv-review\Scripts\python.exe scripts/annotate/api_label_pilot.py prepare
.\.venv-review\Scripts\python.exe scripts/annotate/api_label_pilot.py inspect
.\.venv-review\Scripts\python.exe -m unittest discover -s scripts/annotate -p test_api_label_pilot.py -v
```

Preparation requires NumPy and Pillow. API transport uses the standard library.
The runner reads the first credential in `.env` as OpenAI and the second as Gemini.
Credentials are not printed or included in the frozen input bundle.

Review `outputs/api_label_pilot_v1/index.html`, `prompt.txt`, and `manifest.json`.
Input files, source hashes, settings and runner hash are frozen. Preparation refuses
to overwrite an existing pack. Inspecting the pack makes no network requests.

Only after the user approves this exact scope, run:

```powershell
.\.venv-review\Scripts\python.exe scripts/annotate/api_label_pilot.py run --approve-manifest-sha256 <approved-hash>
```

The runner stores raw responses, provider usage and validated candidate JSONs.
Invalid/truncated annotations are retained but stop the pilot without repair.
On completion, `results.html` shows both models' candidates with a link to the
camera evidence. Schema validity is not semantic correctness. These candidates
are separate from existing annotations and require human review.
