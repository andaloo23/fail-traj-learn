# V4: focused GPT object-identity diagnostic

The user identified incorrect object judgments in the taxonomy annotations. The
earlier identity-specific prompts separated requested and manipulated objects, but
that explicit evidence requirement was absent from the recent taxonomy reruns.
V4 tests its restoration on R001 and R003 using two GPT-6.1 Sol calls. It is not
a new four-episode GPT/Gemini benchmark.

## Change and controls

The prompt asks for a visual identity inventory before segment labeling: stable
object IDs, observed appearance and identity, supported match/mismatch/unresolved,
specific frame/camera evidence, and rationale. The task cannot establish the
identity of whatever is held. Text may only be quoted when legible; nearby or
occluded objects must be tracked separately. Unresolved identities require review
metadata on affected segments, while progress/failure coverage remains complete.

The V3 failure taxonomy and its complete, independent progress/failure scheme are
retained. Same source JPEGs, frame sampling, telemetry, GPT model, low reasoning,
and input/output token limits. No object glossary, privileged simulator names,
reference annotations, or prior model answers are supplied. The prompt and JSON
schema change together; this is not a pure single-sentence prompt ablation.

- [Exact prompt](../scripts/annotate/prompts/failure_taxonomy_identity_v4.txt)
- Frozen artifacts: `outputs/taxonomy_identity_v4/`
- Two requests, $1 total estimated reservation; no retries.
- Actual generation estimate $0.1227345; conservative preflight allowance $0.064862;
  combined $0.1875965. Both responses passed schema and coverage validation.
- Four focused validator tests and browser checks passed.

## Findings

On R001, V3 GPT called the carried carton tomato sauce. V4 calls it orange juice
and cites the ORANGE JUICE text at wrist frame 185. The assistant inspected that
original image and confirmed the visible upside-down words. V4 leaves the exact
identity of the nearby can and red/green package unresolved instead of assigning
tomato sauce from expectations. This supports a concrete identity correction on
this development episode, not general accuracy validation.

On R003, V4 distinguishes the orange-juice carton from the orange-capped brown
bottle subsequently carried. It cites wrist frame 50 for ORANGE JUICE and frame
115 for the bottle's BBQ marking, plus temporal continuity across both cameras.
The assistant inspected those frames. The broad wrong-object conclusion was
already present in V3 GPT; the new result makes its object evidence explicit.
Timing and all other physical/failure judgments remain provisional.

## Review

Refresh [the viewer](http://127.0.0.1:8767/) and select
**V4 — GPT identity check: before / after**. Left is GPT V3; right is GPT V4,
not Gemini. The object inventory includes clickable evidence frames. Only R001
and R003 were run in V4; R002/R004 explicitly show not planned. V1/V2/V3 retain
their original GPT/Gemini comparisons. Raw responses are linked and unchanged.

```powershell
.\.venv-eval\Scripts\python.exe -m unittest discover -s scripts/annotate -p test_api_taxonomy_identity_v4.py -v
.\.venv-eval\Scripts\python.exe scripts/annotate/api_taxonomy_identity_v4.py verify
.\.venv-eval\Scripts\python.exe scripts/annotate/review_taxonomy_pilot.py --prepare-only
```
