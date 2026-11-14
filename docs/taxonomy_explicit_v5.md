# V5: restored explicit evidence instructions

V5 restores the opening identity and physical-evidence instructions from
`scripts/annotate/prompts/identity_v2/progress_failure.md` verbatim, through the
section preceding its old failure categories. It includes the user-supplied
nine-category taxonomy, severity, resetability, and examples verbatim from V2.
Tests check both text requirements.

The output retains complete timeline coverage with independent progress/failure
booleans: progress only, failure only, both, or neither. A brief requested-versus-
manipulated identity check and per-segment frame/camera evidence make claims
reviewable. Uncertainty is explicit and does not leave gaps in the timeline.

This reproduces the earlier prompt's explicitness, not the original Astra
multi-turn demonstration workflow. Models remain GPT-6.1 Sol and Gemini Robotics
ER 2 Preview, both low reasoning, using the same 4 Hz camera samples and telemetry
as V3. Output remains JSON with an 8192-token limit. No object answers, reference
annotations, or simulator identity information are supplied. Prompt and response
schema change together; this is not a single-variable prompt ablation.

- [Exact prompt](../scripts/annotate/prompts/failure_taxonomy_explicit_v5.txt)
- Frozen inputs, requests, raw responses, and ledger: `outputs/taxonomy_explicit_v5/`
- Eight requests completed without retries. Five passed strict validation:
  all four GPT responses and Gemini R002.
- Gemini R001/R003/R004 used `external` instead of the required `agent` camera
  identifier. R003 additionally used `immediately_reattempt` instead of `immediate`.
  The viewer applies only these explicit display aliases, validates the resulting
  complete annotation, and shows a notice. Raw answers and failed strict statuses
  remain unchanged. All eight displayed timelines cover their entire episodes.
- Generation estimate: $0.3786825. Conservative preflight allowance: $0.262593.
  Combined estimate/allowance: $0.6412755, below the $4 reservation.

Refresh [the viewer](http://127.0.0.1:8767/); V5 is selected by default. Earlier
versions remain selectable. Identity and segment evidence have clickable frame
references, and the exact prompt and original responses are linked.

Accuracy remains provisional. On R003, GPT distinguishes a failed grasp from
later wrong-object transport, while Gemini labels wrong-object behavior from
frame zero. On R004, GPT labels frames 135–145 as both progress and collision;
Gemini reports progress without failure. These are model disagreements for human
review, not verified improvements or ground truth.

Validation includes four prompt/contract tests, frozen input verification, and
headless Edge checks across all prompt/episode selections and evidence seeking.
