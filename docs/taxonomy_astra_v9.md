# V9: current Sol versus Astra

The left column reuses the existing V7 GPT-6.1 Sol results unchanged. The right
column contains four new GPT-6 Astra responses. V8 Sol/Luna remains available.

V7's exact prompt and input evidence are retained. Full request payloads compare
equal after removing only the model field: same low reasoning, image detail,
8192-token output limit, response format, and caching behavior. The schema validator,
metadata, telemetry and image bytes also match. No Sol calls are repeated.

- Runner: `scripts/annotate/api_taxonomy_astra_v9.py`
- Prompt: `scripts/annotate/prompts/failure_taxonomy_approach_v7.txt`
- Frozen evidence, raw responses, cost/status ledger: `outputs/taxonomy_astra_v9/`
- Four planned calls; no retries; $10 total reservation.
- Original Sol artifact hashes: `sol_baseline_hashes.json` within the output folder.

Standard short-context rates per million tokens, verified October 5, 2026:

| Type | GPT-6.1 Sol | GPT-6 Astra |
|---|---:|---:|
| Input | $2 | $10 |
| Cache reads | $0.10 | $1 |
| Cache writes | $2.50 | $12.50 |
| Output | $10 | $50 |

Sources: [Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra).
Astra is 5x for input, writes, and output, and 10x for cache reads. With V7 Sol's
exact usage and no cache reads, Astra would cost $1.0441325 versus $0.2088265 for
Sol, excluding conservative preflight allowances. Actual output usage may differ.

Refresh [the viewer](http://127.0.0.1:8767/) for V9. Schema/coverage validation
and model agreement are distinct from annotation accuracy.

All four Astra calls passed strict validation and complete coverage. Generation
estimate from reported usage: $1.0590325, versus $0.2088265 for the original four
Sol calls (5.07x). Neither run received cached-input hits. Astra's conservative
preflight allowance is $0.60697, making its combined estimate/allowance $1.6660025.
These allowances are not claimed as measured preflight charges.

All original Sol artifact hashes remain unchanged. Headless Edge checks passed for
the Sol/Astra column mapping, four complete timelines, segment navigation, and
retention of the V8 Luna comparison, with no browser errors.
