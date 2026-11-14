# Sol V8 / V9.1 matched twelve-episode comparison

## User review and next prompt

The user judged V9.1 better than this V8 adaptation for failure recognition.
[V8.1](oopsie_rich_failure_v8_1.md) is a new candidate that preserves the V9.1
definition and timing rules, then adds categories and explanations to its Yes
intervals. The new prompt is untested; the original paired outputs remain intact.

## Completed, 2026-10-27

All **12/12 new Sol rich annotations** completed and passed Markdown/schema,
coverage and supplied-camera evidence checks. The comparison reuses **36 native
V9.1 Sol responses**. New estimated generation cost is **$2.6291395**, within the
$6 run limit and $5.3255375 conservative preflight ceiling. No Astra calls were
made. The ordinary viewer URL is **http://127.0.0.1:8798/review.html**.

Direct comparison of all twelve frozen request pairs established identical image
data, frame/timestamp labels, camera descriptions, episode/task metadata and API
settings, except the annotation prompt and output-token allowance. Final input
verification and all **315 preserved source-artifact hashes** passed.

Against the preselected V9.1 Sol repeat 1, the extracted V8 binary labels have
**81.12% pooled frame agreement** and **89.83% mean episode agreement**. These are
prompt agreement, not accuracy. V8 marks review-required segments covering
**3,636 of 5,721 source frames**; flags are preserved and agreement includes those
frames. The largest differences are O004 (58.55% agreement), O008 (72.33%), O009
(78.75%) and O003 (84.64%). Review these against video before deciding whether
one richer teacher collection can supply both training targets.

The first publisher encountered a duplicate report-field error after O001/O002
completed. The report was fixed, regression tests were added, and both completed
responses were reused without duplicate API calls. Six offline comparison tests
pass. The native input/output files were not repaired or rewritten.

The final ordinary-URL browser regression passed all **12 episodes and 48 saved
responses**, with **276 video positions, 1,104 binary-label checks, 276 rich-segment
checks and 102 action-button clicks**. Visibility across every split, navigation,
reload, label arrivals, UI-version refresh and frame stepping passed with no
JavaScript errors. Very short action spans have readable action buttons alongside
the proportional timeline; this fixes a pointer-target issue caught by the first
browser pass. The receipt and screenshot are in
`outputs/oopsie_sol_v8_v9_browser_checks/comparison/`.

The requested comparison uses O001-O012 from the approved real OopsieData pilot.
Both sides use GPT-6.1 Sol at low reasoning effort. No Astra calls are requested.

- **V8:** one new native Markdown rich annotation per episode, using the existing
  OopsieData Markdown adaptation in `scripts/distill/oopsie_annotation.md`.
  This preserves actions, physical results, descriptions, failure categories,
  recovery suggestions, evidence and review flags. It is the visual-only
  OopsieData adaptation, not a byte-identical rerun of the historical simulator
  V8 JSON prompt. The exact prompt is frozen in the new run.
- **V9:** the approved V9.1 prompt, reusing all three existing Sol repeats from
  `outputs/oopsie_binary_v9_1_twelve_v1/`. No new binary generation is needed.

The source recordings, tasks, native frame indices, every recorded timestamp,
camera descriptions, camera panel order and frozen image bytes match. There is
no sampling, separate windowing, telemetry, source outcome label or other model
prediction in the new V8 input. V8 has a larger output-token ceiling because its
response is substantially richer. This is a comparison of the two prompt
protocols, not an isolated measurement of explanation tokens alone.

Configuration: `configs/oopsie_sol_v8_v9_twelve_v1.json`.
Output: `outputs/oopsie_sol_v8_v9_twelve_v1/`.

## Collection and preservation

`scripts/distill/compare_v8_v9.py` prepares a fresh directory, verifies the full
V9.1 source, freezes the rich prompt and hardlinks byte-identical image/video
copies. `source_preservation.json` records the source manifest, prompt, settings,
all frozen requests and native response artifacts, and any existing review notes.
Verification rechecks those hashes; native source artifacts are not rewritten.

Preflight counts all twelve exact frozen rich requests. Generation uses an
explicit run-total dollar ceiling, at most two simultaneous calls, an exclusive
collector lock and one saved attempt per episode. Completed responses are parsed
and structurally validated against source coverage and supplied native camera
evidence. Raw API responses and exact returned Markdown are preserved. An
unfinished, invalid or uncertain request is stopped and never automatically
resent; another already-running call is allowed to finish and be preserved.

## Video review

The separate viewer shows original synchronized videos above V8 and V9.1 panels.
Both labels follow scrubbing, frame stepping, playback and segment navigation.
The V8 panel also shows the current original rich action segment, physical result,
description, categories, recovery, uncertainty and evidence. Its full native
Markdown is available in an expandable section and as a download.

For binary comparison only, adjacent V8 segments with the same failure boolean
are merged into a **derived binary projection**. Original rich boundaries and
review flags remain available. Agreement does not treat review flags as trusted
ground truth or as negative labels; reports disclose flagged-frame counts. The
summary compares the two prompts using V9.1 repeat 1 selected in advance; all
three saved V9.1 Sol repeats remain selectable in the viewer.

Labels are visible by default for every episode. The optional blind mode applies
to the whole viewer and persists across navigation/reload. Label arrivals refresh
without losing the selected frame, repeats or review text. Saved human notes are
Markdown. This viewer is separate from the existing Sol/Astra reviewer.

Before reporting completion, run the ordinary-URL browser regression across all
episodes/repeats, rich action boundaries, visibility modes, reloads, simulated
label arrivals and frame stepping, and verify all preserved source hashes.

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/compare_v8_v9.py prepare --config configs/oopsie_sol_v8_v9_twelve_v1.json
.venv-oopsie-distill/Scripts/python.exe scripts/distill/compare_v8_v9.py preflight --run outputs/oopsie_sol_v8_v9_twelve_v1
.venv-oopsie-distill/Scripts/python.exe scripts/distill/compare_v8_v9.py audit-inputs --run outputs/oopsie_sol_v8_v9_twelve_v1
.venv-oopsie-distill/Scripts/python.exe scripts/distill/compare_v8_v9.py collect --run outputs/oopsie_sol_v8_v9_twelve_v1 --budget-usd 6 --workers 2
.venv-oopsie-distill/Scripts/python.exe scripts/distill/check_binary_review_browser.py --url http://127.0.0.1:8798/review.html --browser "C:/Program Files/Google/Chrome/Application/chrome.exe" --out outputs/oopsie_sol_v8_v9_browser_checks/comparison
```

Do not rerun `prepare` on an existing output. Commands that generate annotations
incur API charges; the collected native outputs should be reused for later review.
