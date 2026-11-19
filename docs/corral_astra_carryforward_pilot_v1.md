# Astra rich V8.2 carry-forward pilot

The user authorized one real episode for review and proposed disjoint annotation
parts with the last two frames and previous label carried into the next request.
This is a separate, experimental protocol. Rich V8.2 remains the authoritative
default; native requests and outputs from the earlier 1,000-episode run remain
unchanged. No further original episodes or training are authorized by this pilot.

The runner is `scripts/distill/corral_astra_window_pilot.py`. Its frozen run is
`outputs/corral_astra_rich_failure_v8_2_carryforward_pilot_v1`.

Episode C0052 was chosen as the first held three-camera episode in the frozen
sample order, without using its source outcome. It contains 2,000 native frames
over 66.67 seconds. Every distinct native camera is retained in the existing
280-pixel preparation. The original videos are used for human review.

Six sequential calls label disjoint intervals of up to 350 frames. Each call
after the first receives the preceding two original frames and the complete
native Markdown response from its predecessor. Those two context frames are
outside the interval being labeled. Original frame indices and timestamps are
preserved. The previous label is explicitly described as fallible evidence that
can be contradicted by current observations. Window outcomes are provisional,
and a part ending is not evidence of episode termination.

The next request is constructed only after the previous response validates. Its
preflight records the predecessor response hash. Generation attempts are
journaled before submission; unknown outcomes are not automatically resent.
Only the original episode C0052 may be labeled, with a $12 pilot budget guard.

The disjoint timelines form a deterministic draft. One final Astra call receives
all native part reports, that draft, an overview sampled by elapsed seconds, and
original visual checks near part seams and proposed failure boundaries. It
reconciles complete failure events, their severity/resetability, and one final
episode outcome. This final output is a native Markdown reconciliation response,
not a native single-call full-episode visual annotation. Source-frame coverage
applies to the part stage; the final visual checks are selected evidence.

The pilot uses synchronous standard-price calls for interactive review. Once the
recipe is reviewed, Batch execution could process part 1 across independent
episodes, collect the results, then construct and submit part 2 in another batch.
Chronological dependence is between batches. A single batch file cannot embed a
label that has not yet been generated. Each batch has its own completion window;
several dependent stages can increase total turnaround time.

Review is at `http://127.0.0.1:8812/review.html`, with original video playback,
time-aligned final labels, jumps to part boundaries, links to native part reports,
and Markdown review notes. Runtime costs, any gateway errors, frozen prompts,
and the final annotation are documented in the run's `report.md`. Label quality
requires human review before expanding this protocol.

Verification:

```powershell
.venv-oopsie-distill/Scripts/python.exe -m unittest discover -s scripts/distill -p 'test_corral_astra*.py' -q
.venv-review/Scripts/python.exe scripts/distill/check_binary_review_browser.py --url http://127.0.0.1:8812/review.html --browser 'C:/Program Files/Google/Chrome/Application/chrome.exe' --out outputs/corral_astra_rich_failure_v8_2_carryforward_pilot_v1/browser_checks
```

Passing structural/browser checks establishes faithful coverage and display,
not human correctness. Both the original bulk-run hold and native outputs remain
preserved; pilot results are not automatically promoted into that dataset.

## Second pilot and annotated MP4s

The user reviewed C0052 and then explicitly requested one additional pilot before
deciding whether to proceed. The additional pilot is C0188, the first held
two-camera episode in sample order: 1,800 frames at 15 FPS, lasting 120 seconds.
It uses the same prompts, 350-frame disjoint parts, preceding two frames, and
previous native annotation. Its frozen run is
`outputs/corral_astra_rich_failure_v8_2_carryforward_pilot_v2`; review is at
`http://127.0.0.1:8813/review.html`. The runner only accepts the two explicitly
authorized pilot IDs and keeps each run limited to one original episode.

`scripts/distill/export_astra_carryforward_mp4.py --run RUN_DIRECTORY` creates
derived MP4 review artifacts in `RUN_DIRECTORY/exports_v1`. Each full MP4 keeps
every source frame at its original timestamp, without review holds or repeated
frames. It shows original camera views, final time-aligned labels, a disjoint-part
strip, and persistent thumbnails of the exact two preceding frames supplied to
the current part. The previous part's tail prediction is displayed separately
from the final reconciled annotation. The API received the full prior annotation.

Separate part review MP4s contain the two preceding context frames followed by
the disjoint new interval. Those two prefix frames are explicitly marked
context-only. Source indices remain global. Graphics and final labels are added
for human review and were not model image inputs. Every encoded frame is decoded
to verify its timestamp, final label color, displayed part identifier, and context
role. Original camera timestamps and source file hashes are also checked.

Both MP4 pilots and exact part/frame tables are available at
`http://127.0.0.1:8812/mp4_review.html`. No additional original episodes may be
submitted until the user reviews the second pilot and approves proceeding.
