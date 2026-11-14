# Semantic segmentation rerun

Authorized after the user requested richer phase/failure-reason segmentation and
then said “ok rerun”. Output: `outputs/frame_selection_semantic_v2`.

Final status: 22/24 successful calls (18 annotations, four selections). R001_B timed
out and R001_F was interrupted by the server restart; neither was retried. Known
generation costs total $1.019894 ($0.727105 OpenAI, $0.292789 Gemini). Adding the
$0.631082 token-count allowance and $0.32 held for unknown charges gives conservative
tracked exposure of $1.970976, below the $4.16 cap.

All returned annotations contain the requested phase/reason fields. R003_B omits
the last frame by ending at 279 rather than 280. R004_B uses a closed final interval;
the viewer preserves and flags the notation and plots its literal inclusive end.
The other 16 annotations pass the structural checks. No answers were rewritten.
R001_A increases from two segments to nine; the full comparison is in `RESULTS.md`.

The four-state, full-coverage annotation scheme stays in place. The new common
Markdown prompt explicitly splits changes in task phase, failure reason, concurrent
failures, and meaningful corrections even when the binary labels do not change.
Each segment includes phase, R-style failure types, a specific failure reason,
boundary reason, evidence and confidence. Episode summary and physical events are
also requested. There is no segment-count quota and no assertion that more is better.

A–F run on R001–R004: 20 annotation calls and four Gemini selection calls. Relative
to the previous full-coverage run, images, telemetry, selector/subset prompts,
models and generation settings are unchanged. Human labels are not supplied.
E is rerun and stochastic selections may differ, so cross-run F differences cannot
be attributed solely to the annotation prompt. Episodes have already been inspected;
this is development work, not held-out evaluation.

Total reservations: $4.16 ($3.20 OpenAI, $0.96 Gemini), with no automatic retries.
Each request has token-count preflight, 40,000 input-token ceiling, and 4096 output
tokens including thinking. The 600-second timeout is unchanged. Unknown charges
retain full reservations; estimates use provider usage, not invoices. Older unknown
charges remain in cumulative accounting. The richer outputs are audited for complete
coverage and required semantic fields, and truncation remains a stop condition.

The frozen runner is `scripts/annotate/api_frame_selection_semantic_v2.py`.
`scripts/annotate/summarize_semantic_v2.py` performs offline provenance, cost and
format checks and writes `RESULTS.md` plus `coverage_audit.json`. Segment-count
comparisons describe granularity only; no annotation-quality scores are computed.

R001_B timed out after being sent, with no returned usage or annotation. Its full
reservation remains held. `resume_semantic_v2.py` continues only unsent independent
jobs, checks the frozen manifest, uses an exclusive continuation lock and never
resends a generation. Further transport failures retain their reservations; an
unavailable selection blocks its dependent F call. Budget or validation errors stop
the continuation instead of being bypassed.

The assistant server restart interrupted R001_F after submission. No response or
usage was saved, so its $0.20 reservation remains an unknown-charge allowance. It
was marked stopped and not retried after confirming no runner process remained.
`resume_semantic_after_restart.py` uses a separate exclusive lock and continues only
unsent jobs under the same frozen manifest and reservation ledger.

The usual viewer defaults to **Failure reasons**, with prior runs retained:

```powershell
.\.venv-review\Scripts\python.exe scripts\annotate\review_api_experiment.py
```
