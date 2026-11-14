# V7: useful approach and failure boundaries

V7 adds the three approved labeling rules to V6:

- Useful approach can count as progress before a specific interaction, provided
  there is visible improvement in task-relevant readiness.
- A later wrong-object grasp does not retroactively invalidate an initially useful
  approach. Split when incorrect targeting becomes observable and flag uncertainty.
- Wrong-object targeting is a sequencing/semantic failure. Physical reaching,
  grasp, or manipulation categories require independent failures meeting their
  definitions; they are not action-stage labels.

No categories or schema fields were added. All other prompt text is unchanged,
including the nine-category taxonomy, independent progress/failure booleans, and
complete coverage. No episode-specific desired answers or boundary timestamps were
supplied. R001 motivated the revision, so this is a development-set experiment.

- [Exact prompt](../scripts/annotate/prompts/failure_taxonomy_approach_v7.txt)
- Runner: `scripts/annotate/api_taxonomy_approach_v7.py`
- Frozen inputs, raw responses, and cost/status ledger: `outputs/taxonomy_approach_v7/`
- Same four episodes and GPT/Gemini models/settings as V6; unchanged schema
  validator, metadata, telemetry, and all image bytes verified before evaluation.
- Eight planned calls, no retries; $4 total reservation.

Refresh [the viewer](http://127.0.0.1:8767/) for V7. Earlier versions remain
selectable. Segment annotations remain directly below each model's timeline.
Schema/coverage validation is separate from judging label accuracy.

## Results

All eight calls returned. Six passed strict validation. Gemini R003 and R004 used
`external` instead of `agent` for camera references; the viewer applies its existing
display-only alias and flags it, preserving raw responses and strict failure status.
All eight displayed timelines pass full coverage validation. Headless Edge checks
passed for segment selection across all four episodes, without browser errors.

On R001, GPT now marks [0,25) as progress and starts semantic failure at frame 25.
Gemini still starts semantic failure at frame 0, but no longer misuses physical
reaching/grasp categories for successful execution on the wrong object. Boundary
disagreement remains; the prompt change did not resolve it for both models.

Generation estimate: $0.3835405; conservative preflight allowance: $0.267533;
combined: $0.6510735. No retries or manual label corrections were performed.
