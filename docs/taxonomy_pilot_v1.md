# Categorical failure annotation pilot v1

This pilot follows the user's authorization to experiment with VLMs after freezing
the categorical taxonomy. It is a development comparison, not an accuracy benchmark.

## Results (October 5, 2026)

All eight calls completed and passed structural validation. Estimated generation
cost was $0.3187525; conservative token-count allowance was $0.247421, totaling
$0.5661735 against the $4 reservation. There were no retries or unknown charges.
Eight focused validation/agreement tests passed. Structural validity does not
establish semantic accuracy.

| Episode | GPT annotation | Gemini annotation | Main review question |
|---|---|---|---|
| R001 | Collision [135,150), manipulation [155,275); uncertain [120,135) | Wrong-object action [0,279) | Object identity, release behavior and observable failure onset |
| R002 | No failures | No failures | Independently verify absence of failure |
| R003 | Missed grasp [70,85), wrong-object action [110,210); uncertain [235,280) | Wrong-object action [100,280) | Earlier grasp outcome, category onset, and terminal inactivity |
| R004 | Collision [135,140), medium observed severity | No failures | Does basket displacement constitute harmful/obstructive contact? Is medium severity justified? |

These are model claims, not adjudicated facts. The experiment exposes perception
and definition disagreements in addition to temporal localization differences.
Failure-duration agreement F1 averages 0.492 across the three episodes where
defined, after excluding explicitly uncertain failure-presence intervals. R002
has N/A positive-class F1 because both positive sets are empty. This number is not
accuracy, and the eligible episode/time denominators must accompany it.

The next evaluation step is independent full-video review of object identity,
contact consequences, and recovery onset. Do not tune boundary tolerance to make
these models agree. Establish tolerances from human disagreement and then add
held-out episodes spanning categories absent from this development set.

## Frozen design

- Four previously inspected episodes, R001-R004, each annotated once by
  `gpt-6.1-sol` and `gemini-robotics-er-2-preview`.
- Same chronological external/wrist JPEG pairs and ordinary robot telemetry for
  both models: every five source frames at 20 Hz, plus the last frame. There are
  57 pairs for R001/R003/R004 and 31 for R002. No selectors, oracle facts, prior
  model annotations, human references, tools, or external search in model inputs.
- Low reasoning, OpenAI high image detail, Gemini low media resolution, 8,192
  output tokens including thinking, 80,000 input-token ceiling. Different provider
  image processing remains a confound; this is not a pure architecture comparison.
- Eight requests maximum, $0.50 reserved per request, $4 total estimated ceiling.
  Token-count preflight, separate conservative preflight allowance, no retries,
  persistent reservations before network calls, retained unknown-cost reservations.
  Output limits are larger than the earlier 4,096-token experiments to accommodate
  the richer schema; this is not a strict prompt-only comparison with those runs.
- [OpenAI rates](https://developers.openai.com/api/docs/models/gpt-6.1-sol) and
  [Gemini rates](https://ai.google.dev/gemini-api/docs/pricing) checked October 5,
  2026. Usage-derived costs are estimates, not invoices. Pricing expires December 31.

The exact [prompt](../scripts/annotate/prompts/failure_taxonomy_v1.txt) freezes eight
interval categories and a separate termination event. It distinguishes failure
bouts from category changes within a bout, requires observable evidence, allows
unknown consequences, and separates observed severity from potential risk.
Boundary uncertainty windows do not establish frame-exact accuracy from 4 Hz inputs.

## Artifacts and commands

All inputs, hashes, raw responses, answer text, validated annotations, and cost
ledgers are saved under `outputs/taxonomy_pilot_v1/`. Earlier runs are unchanged.

- [Side-by-side annotations and sampled evidence](../outputs/taxonomy_pilot_v1/review.html)
- [Categorical agreement](../outputs/taxonomy_pilot_v1/agreement.html)
- [Run status and costs](../outputs/taxonomy_pilot_v1/summary.json)
- [Frozen manifest](../outputs/taxonomy_pilot_v1/manifest.json)

```powershell
# Offline checks / report refresh; no API calls.
.\.venv-eval\Scripts\python.exe -m unittest discover -s scripts/annotate -p test_api_taxonomy_pilot_v1.py -v
.\.venv-eval\Scripts\python.exe scripts/annotate/api_taxonomy_pilot_v1.py verify
.\.venv-eval\Scripts\python.exe scripts/annotate/api_taxonomy_pilot_v1.py report
.\.venv-eval\Scripts\python.exe scripts/annotate/summarize_taxonomy_pilot_v1.py
```

The runner's `prepare` command creates a new frozen pack and refuses overwrite.
Its `run` command sends paid requests only for unreserved cells. Existing cells
are never resent, including failed or interrupted requests.

## Evaluation interpretation

The offline summary measures **model agreement only**, using failure-duration F1
and per-category duration F1. An interval marked uncertain by either model is
excluded; eligible coverage is reported. Unmarked time otherwise represents only
a provisional model negative, not verified negative supervision. Semantic doubts
inside a positive segment remain visible in its uncertainty text.

For episodes without uncertain failure-presence intervals, the summary also
reports one-to-one failure-bout F1 at temporal IoU 0.25/0.50/0.75 and boundary F1
at 0.10/0.25/0.50 seconds. Episode endpoints are excluded from boundary detection.
Whole-event scores are withheld on episodes with uncertain intervals because
masking or clipping can invent event boundaries. Precision/recall use Gemini as a
comparator for bookkeeping; Gemini is not ground truth. Both-empty positive sets
have N/A F1. No prose similarity or composite quality score is used.

Human review must establish object identity, failure presence, category transitions,
and plausible boundary windows before deciding which model is correct. Severity
and resetability are retained for review but not ranked automatically. No existing
reference approval statuses are altered, and no annotations enter training.

These four episodes do not guarantee coverage of all taxonomy categories, damage
levels, or reset requirements. A broader independently annotated sample is needed
before calling this a benchmark or drawing generalization conclusions.
