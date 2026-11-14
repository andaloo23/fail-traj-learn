# Uniform, points, and windows: matched-budget development screen

User authorized this comparison on R001–R004. Output directory:
`outputs/frame_selection_windows_v1`. No human labels are supplied to either model.

Final status: 18/20 planned calls successful (11 annotations, seven selectors).
R001_SP timed out without returned usage; its $0.12 reservation remains held, and
R001_P was skipped without sending a generation. There were no retries. All 11
annotations pass coverage/required-field checks. The offline audit verified matched
unique-image budgets, common overviews, prompt/telemetry consistency, original
candidate bytes, frozen selection expansion and usage-derived costs.

Known generation estimate: $0.742190. Conservative token-count allowance: $0.472730.
Including $0.12 for the unknown charge gives $1.334920 against the $3.36 cap.
All three conditions are available on R002–R004; R001 has U and W. Per-episode
pipeline costs and exact selections are in `RESULTS.md`. No semantic quality winner
has been established; these are model annotations awaiting human review.

Each episode has five calls: U (GPT uniform), SP (Gemini point selection), P (GPT
selected points), SW (Gemini window selection), W (GPT expanded windows). There
are 20 calls total: 12 GPT annotations and eight Gemini selections. Models and
annotation prompt/settings are unchanged from the semantic-v2 run. All three GPT
conditions receive the same subset-handling and semantic annotation instructions.
Only source-frame lists and associated images differ. No selector reasoning or
semantic labels are forwarded to GPT; it assigns the final labels and boundaries.

## Image budgets and deterministic sampling

R001/R003/R004: 24 unique synchronized camera pairs per GPT call. R002: 12.
U samples the full source frame range evenly, rounding ties upward. Six overview
pairs (four for R002) are evenly selected from U and also included in P and W.
These overview pairs may include original frames outside Gemini's candidate pool;
the same overview images reach GPT in every condition.

SP selects 18 additional distinct candidate timestamps (eight for R002), excluding
overview duplicates. SW selects three disjoint inclusive windows (two for R002),
each `[start, start+10]`: 0.5 seconds at 20 FPS. Starts must be from the candidate
pool and leave the whole window inside the episode. Windows are strictly ordered
and non-overlapping; invalid selections are rejected, not semantically repaired.

Each window yields six pairs (four for R002), sampled evenly from its 11 original
frames. If a target sample duplicates an overview frame, choose the nearest unused
frame inside that window, ties to the earlier frame. Exact final unique-image counts
are enforced. All images use original 256×256 camera views and JPEG quality 90;
existing candidate JPEGs are copied byte-for-byte. No crops or model image edits.

Gemini sees the unchanged every-five-source-frame candidate pool plus the last frame,
with both cameras and the same telemetry. It sees no extra window interior images.
It is given overview indices as metadata without being told what unseen frames show.
Selection prompts share evidence priorities and differ in their selection contracts.
GPT receives identical ordinary telemetry in U/P/W.

## Budget and provenance

Maximum reservation $3.36: 12 × $0.20 OpenAI and 8 × $0.12 Gemini. Each call has a
token-count preflight, 40,000 input-token ceiling, 4096 output tokens including
thinking, low reasoning, and the existing Gemini low media resolution. Timeout is
600 seconds and there are no automatic retries. Preflight plus maximum estimated
generation must fit the call reservation. Unknown charges retain full reservations.
Transport errors permit independent unsent jobs to continue; missing selection
blocks only its dependent annotation. Other errors halt for inspection.

Frozen runner: `scripts/annotate/api_frame_selection_windows_v1.py`. Offline audit:
`scripts/annotate/summarize_windows_v1.py`. Reports include per-call and selector-plus-
annotator costs, exact selected frames/windows, structural warnings and provenance.

## Human review

Compare P versus W at the same image budget; U checks whether selection justifies
its extra cost. Review identity evidence, coverage before/after important transitions,
and persistent failures separately from GPT's final boundary/reason correctness.
Use full-video human review to establish needed transition windows; original R model
annotations are not ground truth. Segment counts alone are not quality metrics.

This is a development screen on inspected episodes, one sample per condition.
Window selection changes local density as well as temporal grouping, and cannot
isolate those mechanisms. It also cannot reveal a transition Gemini never notices.
Reducing Gemini's input sampling is deferred to a later experiment.

The usual viewer defaults to **Points vs windows**, with all previous runs retained:

```powershell
.\.venv-review\Scripts\python.exe scripts\annotate\review_api_experiment.py
```
