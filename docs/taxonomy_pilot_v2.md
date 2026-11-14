# Taxonomy pilot v2: original user wording

## Completed run

Eight generation calls returned complete answers, with no retries. GPT's four
answers passed the original strict schema. All four Gemini answers used `id`
instead of `episode_id`; their strict validation remains failed in the ledger.
Their segment payloads pass validation after that single envelope-key mapping.
The viewer applies this mapping for display only, prominently marks it, and links
the unmodified answer. No model label, interval, description or consequence is
changed. These display mappings are not approved annotations or training data.

Generation estimate: $0.3025945. Conservative preflight allowance: $0.249753.
Combined estimate/allowance: $0.5523475; no unknown-cost reservations remain.
Five focused tests passed. Browser checks verified all 16 annotations across
V1/V2, warning labels, episode/version switches, disagreement jumps and camera
playback without JavaScript errors.

GPT now groups R001 into [135,270), with grasp/manipulation/collision labels.
Its R003 intervals are [55,85) grasp and [85,280) sequencing/semantic. It still
flags basket contact in R004, now [130,145), low severity and minor reset. Gemini
still calls R001 wrong-object behavior, identifies R003 manipulation/semantic
failure, and reports no failures for R002/R004. These remain model claims, not
evidence that the revised prompt is more accurate. Human review is required.

The user found the adapted v1 prompt unsatisfactory and requested the taxonomy
essentially word for word. V2 restores the user's definitions, nine categories,
examples, severity criteria (actual and potential damage), resetability criteria,
and segment start/end instructions. Numbering and indentation are cleaned up.

The only appended instructions describe the existing image/telemetry inputs and
the minimal JSON response format. They do not add a bout hierarchy, category-set
merge rule, uncertainty intervals, boundary uncertainty windows, separate risk
score, or separate termination event. Sudden episode termination is again an
allowed failure category. Estimates can use source-frame indices between sampled
images, so their numerical precision must not be mistaken for observed precision.

Exact source: [prompt](../scripts/annotate/prompts/failure_taxonomy_v2.txt).
Frozen run copy: `outputs/taxonomy_pilot_v2/prompt.txt`.

## Controlled rerun

The same four development episodes and two models are used as in
[v1](taxonomy_pilot_v1.md): GPT-6.1 Sol and Gemini Robotics ER 2 Preview. Settings
are identical, including low reasoning, provider image-resolution settings,
8,192 output tokens, 80,000 input-token ceiling, $0.50 per-call reservation and
$4 maximum estimated reservation for eight calls. No automatic retries.

Both input JSON and sampled image bytes are verified identical across prompt
versions. Prior labels, human references and simulator outcomes are not sent.
Inputs and outputs are saved separately in `outputs/taxonomy_pilot_v2/`; v1
generation artifacts and its frozen runner remain unchanged.

The semantic task and output schema changed together to follow the original
taxonomy. A change in segment count alone does not establish improved accuracy.
V1 and v2 categorical metrics should not be treated as equivalent definitions.

## Review

The [local viewer](http://127.0.0.1:8767/) has a Prompt selector for V1 and V2 and
defaults to V2. Each version offers GPT/Gemini timelines, disagreement jumps,
original and sampled camera playback, and an exact-prompt link. Notes are stored
separately per episode and prompt version in the browser; they are not submitted
as approved references. Earlier notes under the V1 key are preserved.

```powershell
# Validate schema and restored instructions; no API requests.
.\.venv-eval\Scripts\python.exe -m unittest discover -s scripts/annotate -p test_api_taxonomy_pilot_v2.py -v
.\.venv-eval\Scripts\python.exe scripts/annotate/api_taxonomy_pilot_v2.py verify
# Refresh both versions after new results arrive.
.\.venv-eval\Scripts\python.exe scripts/annotate/review_taxonomy_pilot.py --prepare-only
# Start the viewer if it is not already running.
.\.venv-eval\Scripts\python.exe scripts/annotate/review_taxonomy_pilot.py
```

The schema validator checks bounds, chronological order, allowed categorical
values and required text fields. It does not enforce the removed v1 interpretation
of continuous bouts or category-set transitions. Structural validation is not
semantic approval. Raw answers and usage are retained even when validation fails.
