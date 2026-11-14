# H human-reference evaluation

This experiment labels H001-H012 with three frozen pipelines and compares their
outputs against the user's designated human ground truth. Outputs are in
`outputs/h_pipeline_evaluation_v1/`; scored results and timestamped differences
are in `evaluation/RESULTS.md` and `evaluation/*_differences.md`.

## Controlled conditions

| Condition | Input selection | Annotation model |
|---|---|---|
| U | Uniform frames | GPT-6.1-sol |
| P | Common overview plus Gemini-selected points | GPT-6.1-sol |
| W | Common overview plus dense samples inside Gemini-selected windows | GPT-6.1-sol |

Selection uses Gemini Robotics ER 2 preview. Prompts are copied unchanged from
the preceding point/window experiment. All conditions use the same task,
ordinary telemetry, original image quality, annotation prompt and GPT image
budget for each episode. There are 24 camera pairs per condition, reduced to 12
for episodes with at most 150 frames. Gemini sees the same 4 FPS candidate pool
for point and window selection. Every camera pair contains agent and wrist views.
Windows span 11 source frames; GPT assigns the semantic boundaries.

The 60-call plan comprises 36 GPT annotations and 24 Gemini selections. The
maximum reserved allowance is $10.08 ($7.20 OpenAI, $2.88 Gemini). Two episode
workers share a locked reservation ledger. No automatic retries are allowed.
Provider usage, returned model, token counts, raw answers, request evidence and
cost estimates are retained per call. Input-count preflight allowances are
reported separately from estimated generation charges; neither is an invoice.

## Reference and scoring

Human files are frozen separately with SHA-256 hashes. Requests contain only
the task, cameras and allowlisted ordinary telemetry. H labels, simulator event
arrays, simulator state labels and contact-derived labels are not model inputs.
No in-context H examples are supplied in this run.

All twelve human references record `privileged_simulator_contacts` annotation
assistance. We score their human-authored segments, not simulator event/state
arrays. This provenance must remain visible in reports. These are the user's
designated references, not independently re-adjudicated four-state labels.
H also appeared in historical few-shot development, so this is a development
benchmark rather than a wholly unseen final test.

H uses mutually exclusive progress, failure and neutral labels. For compatibility,
predicted progress-and-failure projects to failure; progress-only stays progress;
neither projects to neutral. Original annotations remain unchanged. Consequently
this benchmark cannot validate the independent four-state annotation scheme.

Metrics include time-weighted legacy class accuracy, pooled failure precision,
recall and F1, failure-type agreement, one-to-one boundary matching at several
tolerances, segment overlap and local description embedding cosine. The headline
boundary tolerance is 250 ms (five source frames). Extra semantic phases can
lower boundary precision even when they are reasonable; inspect those differences.
Cosine measures textual resemblance, not factual correctness. It uses local
MiniLM embeddings and spends no API credits. Aggregates compare only the same
fully completed, structurally valid U/P/W episodes and retain missing outputs in
the inventory. These are not the withdrawn simulator-reference event scores.

## Reproduce scoring and review

```powershell
.\.venv-eval\Scripts\python.exe scripts\annotate\evaluate_h_pipelines.py
.\.venv-review\Scripts\python.exe scripts\annotate\review_api_experiment.py
```

Scoring verifies frozen inputs and reference hashes, rebuilds request evidence,
checks saved answers against raw responses and recomputes costs from raw usage.
The viewer opens H by default. Select H to inspect human bars, or U/P/W to inspect
model bars and the linked timestamped difference report. Model-frame playback
shows exactly the supplied images; H playback uses the full episode.

The paid runner has already been launched for this experiment. Do not launch it
again to reproduce evaluation: both commands above operate on saved artifacts.
