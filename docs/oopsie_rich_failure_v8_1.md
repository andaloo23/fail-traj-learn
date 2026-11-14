# V8.1 rich failure annotation based on V9.1

## Completed after credit reload, 2026-10-27

All **36/36 V8.1 Sol responses** completed and passed structural validation:
three independent identical requests for each of O001-O012. The six responses
completed before the credit stop were reused; **30 additional Sol calls** ran
after the user replenished credits. **No new Astra calls** were made. The user
confirmed Sol-only collection; this preference is recorded in AGENTS.md.

Estimated cost for the complete 36-response run is **$2.6765533**, including
$1.2204835 before the stop and $1.4560698 after resuming. The $12 run-total limit,
frozen prompt, requests, images and preflight receipts were unchanged.

Binary results:

- **9/12 episodes have exact 3/3 agreement**, including all segment boundaries.
- **5,499/5,721 source frames (96.12%)** have unanimous labels across all three
  repeats. O004, O008 and O012 contain the 222 disagreement frames.
- O004 has 87.31% frame unanimity; O008 has 89.22%; O012 has 99.50%, with only
  source frame 89 differing in the latter.
- O009's binary timeline matches across all three repeats, but its category sets
  differ. Category sets agree in the other three positive-containing episodes
  with exact binary timelines: O003, O005 and O011. Negative-only episodes have
  no category agreement to assess. Explanation semantics require video review.
- Pooled agreement with the preselected V9.1 Sol repeat 1 is **96.63%** across
  the three new repeats. This measures teacher agreement, not recognition accuracy.

For context, the saved V9.1 Sol baseline itself has exact binary 3/3 agreement
on 8/12 episodes and 95.94% frame unanimity. These are descriptive pilot results,
not evidence that the new prompt is more accurate.

The comparison remains at **http://127.0.0.1:8799/review.html**. Both panels use
Sol: new V8.1 on the left and preserved V9.1 on the right. All three repeats are
selectable. `report.md` lists each disagreement interval; the viewer separately
shows current-frame consensus and whole-episode agreement.

Preservation checks passed for all 315 original V9.1 artifacts, all 41 files
frozen/preserved at resume, and both archived credit-rejection attempts. All 36
completed API response IDs are distinct. The resume receipt is
`outputs/oopsie_rich_failure_v8_1_twelve_v1/resume_20261028T020150Z.json`.
The earlier credit-stop receipts below remain historical records.

The final ordinary-URL browser check passed all twelve episodes and all 72
available responses (36 new V8.1 plus 36 saved V9.1): **167 video positions,
1,002 binary-label checks and 501 enrichment checks**, with no JavaScript errors.
Navigation, repeat selection, reloads, global visibility, simulated label arrivals,
frame stepping and UI-version refresh passed. The checker waits for DOM and
explicit video readiness; a network-idle wait had timed out on video activity.
Receipt: `outputs/oopsie_rich_failure_v8_1_browser_checks/completed/browser_check.json`.

### Action outlines and visible explanations

The viewer keeps the binary failure/non-failure colors and adds outlined action
boxes **on the left panel only**, so an action such as grasp can overlap either
binary label. These are derived from the already saved V8 Sol repeat 1 actions,
not from V8.1 or V9.1. The source is stated beside the layer. V8.1 still generated
only binary labels plus failure categories/explanations; V9.1 generated only the
binary labels. No new teacher calls were made for this display change.

The right V9.1 panel contains its binary output without action overlays. An initial
display applied the same old action track to both panels; this was removed from
V9.1 after the user pointed out the misleading attribution. Primary labels,
native requests, responses, original rich actions and review notes are unchanged.

`review_options.json` selects the saved action-source run for this derived view.
Publication verifies matching episode/frame/camera evidence and native action
annotation hashes. Adjacent pieces of the same V8 action are merged for outlining
without importing any V8 failure judgments. Categories and explanations for all
V8.1 failure intervals are visible below the bar even when paused on a No frame.

## Credit stop, 2026-10-27

Generation completed **6/36 native V8.1 Sol responses**: O001-O006, repeat 1.
O007/O008 repeat 1 were explicitly rejected with HTTP 429
`credit_balance_exhausted`. Both rejection attempts are preserved. The collector
stopped without retrying; no other new calls were submitted. Estimated cost for
the six completed responses is **$1.2204835**.

**No episode has three completed repeats, so no 3/3 agreement result exists yet.**
The six first repeats have 98.48% pooled frame agreement with the preselected
V9.1 Sol repeat 1. This is preliminary teacher agreement on the completed subset,
not repeatability or accuracy. Four of those six match the reference exactly;
O003 and O004 have boundary differences.

All twelve exact requests passed token preflight and direct image/metadata
comparison against the frozen V9.1 requests. The conservative ceiling for all 36
generations is $10.1223825, within the $12 run limit. Completing the remaining
30 responses requires replenished API credits. Reuse the six completed responses;
archive only the two explicit credit-rejected attempts, preserving their bytes,
before resuming. Unknown submissions or attempts with a model response must never
be silently archived or resent. No prompt/input change is needed for continuation.

The partial-run reviewer passed the ordinary-URL regression across all twelve
episodes and all 42 available responses (six new plus 36 V9.1 references): 143
video positions, 501 binary-label checks and 72 enrichment checks, including
navigation, reloads, visibility modes, simulated label arrivals and frame stepping.
No JavaScript errors remained. This verifies review behavior for available labels,
not completion of the requested three-repeat experiment. The eight enrichment
tests and six legacy comparison tests pass. The browser receipt is under
`outputs/oopsie_rich_failure_v8_1_browser_checks/current/`.

## Three-repeat diagnostic, requested 2026-10-27

The user authorized rerunning the new prompt and checking 3/3 agreement.
`configs/oopsie_rich_failure_v8_1_twelve_v1.json` defines **36 new Sol calls**:
O001-O012, three independent identical requests per episode, low reasoning,
all recorded timestamps and the byte-identical synchronized camera strips from
the approved V9.1 run. No Astra calls are planned. Original runs remain preserved.

Run directory: `outputs/oopsie_rich_failure_v8_1_twelve_v1/`.
Ordinary comparison URL: **http://127.0.0.1:8799/review.html**. The V8.1 side has
three selectable repeats; the other side reuses the three saved V9.1 Sol repeats.
`report.md` and `comparison_results.json` record current collection progress and
agreement; a pending episode cannot be marked 3/3.

Here, **binary 3/3 exact agreement** means all three canonical Yes/No timelines
are identical, including every boundary. **Three-way frame unanimity** counts
source frames for which all three labels agree; it is distinct from average
pairwise agreement. Conflicting source-frame intervals are listed explicitly.
Category sets are compared when the binary intervals match, with category order
ignored. All-negative cases have no category agreement to assess. Explanation
wording is not expected to match; semantic quality requires human review.

The new native Markdown parser checks binary coverage, exact correspondence of
enrichment boundaries to Yes rows, supported category identifiers and source
frame/camera reference presence. These checks do not prove that the visual claims
are correct. Native responses and frozen requests remain append-only; stopped or
unknown attempts are not automatically resent.

```powershell
.venv-oopsie-distill/Scripts/python.exe scripts/distill/compare_v8_v9.py prepare --config configs/oopsie_rich_failure_v8_1_twelve_v1.json
.venv-oopsie-distill/Scripts/python.exe scripts/distill/compare_v8_v9.py preflight --run outputs/oopsie_rich_failure_v8_1_twelve_v1
.venv-oopsie-distill/Scripts/python.exe scripts/distill/compare_v8_v9.py audit-inputs --run outputs/oopsie_rich_failure_v8_1_twelve_v1
.venv-oopsie-distill/Scripts/python.exe scripts/distill/compare_v8_v9.py collect --run outputs/oopsie_rich_failure_v8_1_twelve_v1 --budget-usd 12 --workers 2
.venv-review/Scripts/python.exe scripts/distill/check_binary_review_browser.py --url http://127.0.0.1:8799/review.html --browser "C:/Program Files/Google/Chrome/Application/chrome.exe" --out outputs/oopsie_rich_failure_v8_1_browser_checks
```

The user reviewed the matched twelve-episode Sol comparison and judged V9.1
better than the existing rich V8 adaptation for failure recognition. This new
prompt keeps the successful binary task central and adds the requested failure
categories and explanations:

`scripts/annotate/prompts/rich_failure_v8_1.md`

## What is preserved

The V9.1 text from "Watch the entire robot episode" through the end of its
segment-boundary instructions is copied verbatim. This includes the failure
definition, all nine recognition criteria, the unfinished-grasp/empty-gripper/
pause/recording-ending rules, and the whole-interval timing instructions.

The primary output is still a complete, half-open binary segment partition with
adjacent equal labels merged. Action changes and category changes do not split
the binary timeline. The table can be extracted as a derived binary training
target, while the native rich Markdown remains preserved.

## What is added

After the table, each Yes interval receives one annotation with the exact same
boundaries, supported category identifiers and a concise explanation grounded in
source frame/camera observations. The category identifiers match the existing
taxonomy. Multiple categories require independent visual support; Unclear is an
explicit category-uncertainty marker when failure is established but its type
cannot be supported. This marker is not an additional taxonomy category.

The first revision asks only for binary segments, failure categories and failure
explanations. It does not restore V8's full action/identity/recovery/severity/
resetability schema. This keeps the experimental change aligned with the user's
requested enrichment. A category/explanation task can later be expanded separately.

## Example response shape

This is an illustrative format example, not an annotation of any real episode:

```markdown
# Episode: EXAMPLE

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 30 | No |
| 30 | 45 | Yes |
| 45 | 100 | No |

## Failure annotations

### Failure 1

- Frames: 30-45
- Categories: grasp
- Explanation: At frame 30 in wrist_camera, the closed gripper moves away empty while the target remains on the table; scene_camera at frame 36 confirms that the target was not acquired. The failed acquisition does not advance the requested pick-and-place task.
```

An episode with no observable failure has a single No row covering its source
frames and `None` under Failure annotations.

## Versioning and evaluation

This is a new prompt, not a correction to frozen V8/V9.1 artifacts. The collector
now dispatches to `failure_enrichment_v8_1.py` for this output contract and supports
independent repeats while preserving the legacy V8 schema. No training has started.

The diagnostic uses the same twelve real OopsieData episodes, all recorded frames
and cameras, and Sol only. Each exact request and native Markdown response is
preserved. The prompt is frozen before generation. Compare all repeats to the approved V9.1
Sol labels, focusing on recognition, onset/offset placement and failure IoU as
well as frame agreement. Assess category/explanation quality separately.

Keeping the definition text unchanged does not guarantee that a richer response
will preserve the model's binary judgments. A single call can produce both
training views economically, but its recognition must be checked. If enriching
within one call degrades binary recognition, a separate downstream annotation
pass over frozen V9.1 intervals can enforce boundary/label preservation by
validation. That would be an enrichment pipeline, not an independent recognition
evaluation.
