# V8: current Sol versus Luna

The left column reuses the existing V7 GPT-6.1 Sol annotations unchanged. The right
column contains new GPT-6 Luna responses on the same four episodes. No Sol or Gemini
requests are sent by this experiment.

The V7 prompt is reused byte-for-byte. Input image bytes, metadata, telemetry and
validator are identical. Both models use low reasoning, high image detail, 8192
maximum output tokens, and the same request structure. Caching was not restructured
during this comparison. The sole inference configuration change is the model name.

- Runner: `scripts/annotate/api_taxonomy_luna_v8.py`
- Prompt: `scripts/annotate/prompts/failure_taxonomy_approach_v7.txt`
- Frozen inputs, responses, and ledger: `outputs/taxonomy_luna_v8/`
- Four calls, no retries, $0.20 total reservation.
- Luna rates per million tokens: $0.10 input, $0.01 cache reads, $0.125 cache writes,
  $0.50 output. [Official pricing](https://developers.openai.com/api/docs/models/gpt-6-luna)
- `sol_baseline_hashes.json` records hashes of the original V7 artifacts for
  checking that the comparison leaves them unchanged.

Refresh [the viewer](http://127.0.0.1:8767/) and select V8. Both column headings
identify the actual models. Earlier prompt/model comparisons remain available.
Schema validation and model agreement do not establish annotation accuracy.

All four Luna responses passed strict validation and complete coverage. Generation
estimate: $0.010831825; conservative preflight allowance: $0.0060697. Combined:
$0.016901525. All saved Sol artifact hashes remain unchanged. Headless Edge checks
confirmed the correct model headings, original Sol annotations on the left, Luna
annotations on the right, and working segment navigation on every episode.
