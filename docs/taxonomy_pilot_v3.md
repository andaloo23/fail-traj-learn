# Taxonomy pilot v3: complete independent progress/failure coverage

## Completed rerun

All eight generation calls returned complete answers. All eight segment payloads
cover 100% of their episode with explicit progress/failure booleans and no gaps or
overlaps. Seven responses passed the strict envelope schema. Gemini R001 also
echoed input metadata (`task`, `n_frames`, `fps`, `sampled_frames`); its strict
validation remains failed. The viewer ignores only those verified matching extra
envelope fields for display, flags the discrepancy, and leaves every segment and
label unchanged. No missing labels were synthesized.

Generation estimate: $0.3204975; conservative preflight allowance: $0.252945;
combined estimate/allowance: $0.5734425. No retries or unknown-cost reservations.
Six focused tests passed. Browser checks verified all 24 annotations across
V1/V2/V3, disagreement seeking, and both-positive rendering without JavaScript
errors. `outputs/taxonomy_pilot_v3/coverage_audit.json` records the per-episode,
per-model coverage and frame counts for all four states.

Examples of actual V3 outputs: GPT labels both progress and failure on R001 and
R004; Gemini does so on R003. GPT labels explicit neither periods on R003/R004.
Both models label the full R002 episode as progress without failure. These are
model judgments, not adjudicated accuracy results.

The user requested a rerun with progress segments, independent progress and
failure judgments, and no unlabeled time. V3 partitions every episode into
consecutive half-open intervals covering [0,n_frames). Each interval has explicit
boolean `progress` and `failure`: progress only, failure only, both, or neither.
Neither is an explicit judgment, not a gap. Negative model judgments are still
provisional; complete structural coverage is not human verification.

The V2 failure taxonomy and examples are retained. Failure categories, recovery,
severity and resetability are required for failure-positive intervals, including
intervals also labeled progress. Nonfailure intervals have empty categories and
null failure-only fields. Every interval includes a description. Complete coverage
and independent labels supersede exclusive-progress implications in the original
failure-only wording. No labels are filled in or repaired after generation.

## Experiment

- Four episodes R001-R004, GPT-6.1 Sol and Gemini Robotics ER 2 Preview, eight
  generation calls maximum. Separate output: `outputs/taxonomy_pilot_v3/`.
- Same camera JPEGs, source frames, telemetry, model settings, token limits and
  cost controls as V2. The episode metadata uses `episode_id` to match the response
  schema, avoiding V2's `id` spelling conflict. The input content is otherwise
  unchanged. Both models receive identical annotations instructions.
- $0.50 per-call reservation, $4 total estimated reservation, token preflight,
  no automatic retries, and raw response/cost retention.
- [Exact prompt](../scripts/annotate/prompts/failure_taxonomy_v3.txt).

The validator rejects empty partitions, missing booleans, gaps, overlaps, omitted
tails, and inconsistent failure-only fields. Tests cover all four states, including
simultaneous progress and failure and explicit neither. No human references or
previous model outputs are supplied to either model.

## Viewer

Refresh [the local viewer](http://127.0.0.1:8767/), which defaults to V3. The Prompt
selector preserves V1/V2. Green = progress only; red = failure only; striped = both;
gray = neither. Disagreement jumps compare both booleans and failure categories.
The viewer renders raw categorical judgments without converting omitted intervals
from earlier versions into verified negatives. Notes are isolated by prompt version.

```powershell
.\.venv-eval\Scripts\python.exe -m unittest discover -s scripts/annotate -p test_api_taxonomy_pilot_v3.py -v
.\.venv-eval\Scripts\python.exe scripts/annotate/api_taxonomy_pilot_v3.py verify
.\.venv-eval\Scripts\python.exe scripts/annotate/review_taxonomy_pilot.py --prepare-only
```

V3 changes the annotation contract, so its raw segment counts are not directly
comparable to failure-only V2 counts. Human review must assess label correctness
and boundaries before claiming improved annotation quality.
