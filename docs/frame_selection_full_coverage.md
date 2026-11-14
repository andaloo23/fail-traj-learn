# Full-coverage annotation rerun

The user authorized rerunning the pipeline after adopting the four-state annotation
scheme. This is a separate run in `outputs/frame_selection_full_coverage_v1`.

Completed 23/24 calls: 19 full-coverage annotations and four selections. All 19
annotations pass interval/label validation, with no coverage warnings. R004_B has
no returned annotation. Known generation cost is $0.793846 ($0.558241 OpenAI,
$0.235605 Gemini); the $0.595034 token-count allowance plus $0.12 reserved for the
unknown R004_B charge bring conservative tracked exposure to $1.508880.

All six conditions A–F are rerun on R001–R004: 20 annotation calls and four selection
calls. A is GPT on all candidate frames, B is Gemini on all candidates, C is GPT on
all candidates with subset instructions, D is GPT on uniform subsets, E is Gemini
frame selection only, and F is GPT on E's selected frames.

The shared Markdown annotation prompt now requires a consecutive partition of the
whole episode with explicit progress and failure yes/no, per-axis confidence, and
review flags. The selector and subset-handling prompts are byte-identical to the
specific-prompt run. Images, telemetry, models, generation settings and sample
budgets are unchanged. No human annotations or examples are supplied. E is rerun,
so its selections may vary; cross-run F changes cannot be attributed solely to the
new annotation prompt. This remains development work on previously inspected episodes.

Reservations total $4.16 ($3.20 OpenAI, $0.96 Gemini). Every request is counted before
generation and checked against its reservation, including a conservative token-count
allowance. Output is limited to 4096 tokens including thinking, transport timeout is
600 seconds, and retries are disabled. An unknown in-flight charge retains the full
reservation. Provider usage drives estimates; invoices are not queried.

The frozen runner is `scripts/annotate/api_frame_selection_full_coverage_v1.py`.
The offline audit `scripts/annotate/summarize_full_coverage.py` checks provenance,
saved responses, usage costs and complete label coverage. Invalid outputs are flagged
for human review, preserved verbatim, and not automatically repaired or regenerated.

The standard viewer opens this run by default and keeps earlier runs in its Run menu:

```powershell
.\.venv-review\Scripts\python.exe scripts\annotate\review_api_experiment.py
```

See the run's `RESULTS.md`, `costs.csv`, `cost_summary.json`, and `coverage_audit.json`
for completion, costs and structural warnings. Structural validity is not a measure
of semantic annotation quality; these outputs still require human review.

R004_B disconnected after generation was sent, without a response or usage record.
It was not retried, and its $0.12 reservation remains an unknown-charge allowance.
The separate `resume_full_coverage_remaining.py` continuation only sends the still
unsent R004 C–F jobs after checking frozen inputs and prior attempt records. It
retains the original budget ledger and uses an exclusive continuation lock.
