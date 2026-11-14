# Historical annotation scheme: complete progress/failure coverage

This earlier prompt experiment is retained for labeling provenance. New OopsieData
work follows the versioned rich/binary protocols in [the pipeline guide](oopsie_distillation.md).

Every episode is partitioned into consecutive, non-overlapping segments covering
`[0, n_frames)`. Every segment explicitly assigns both progress and failure:

| Progress | Failure | Meaning |
|---|---|---|
| no | no | Neither task advancement nor an unsuccessful/harmful action in this interval |
| yes | no | Task advancement without a simultaneous failure |
| no | yes | Failure without simultaneous task advancement |
| yes | yes | Task advancement and failure occur together, e.g. moving the correct object while causing a harmful side effect |

These are two independent binary judgments. Do not equate movement with progress,
or lack of progress with failure. A pause can be no/no; a sustained failed attempt
can be no/yes. Judge relative to the language task and visible evidence.

Start a new segment when either judgment changes, or when a meaningful action phase,
failure reason, concurrent failure, object/destination, or recovery attempt changes.
Adjacent intervals must share their boundary; the first starts at 0 and the last ends
at n_frames. Identical binary labels and failure types do not require merging:
wrong-object acquisition, transport, and placement can be distinct semantic segments.
Merge only materially equivalent behavior/reasons; do not impose a segment quota or
split merely at every supplied frame. A persistent error can span several segments.

Uncertainty is metadata, not a fifth semantic class. Assign the best-supported pair
and mark low-confidence or ambiguous judgments as provisional with review required.
Describe which judgment is uncertain and why. An uncertain/provisional no is not
a verified negative and should be excluded from definitive negative training labels
until human adjudication. Never use no/no as an automatic default for missing evidence.

The Markdown output has Object identity check, Episode summary, Segments, Events,
and Limitations sections.
Each segment records an explicit half-open frame interval, progress yes/no, failure
yes/no, confidence for each judgment, review-required yes/no, description, evidence,
uncertainty, failure categories (or none), action phase, failure types, a specific
failure reason, and the reason for its boundary. Failure types restore the original
R vocabulary: missed_target, lost_control, wrong_action, collision, timeout, other.
Multiple types are allowed. Use none for non-failure, and unknown only for a
provisional unresolved failure requiring review. Explanations must describe observed
behavior and task consequences, without inventing hidden perception/planning causes.

Key physical events have supported source-frame windows, evidence, confidence and
an explanation. Physical events do not themselves determine progress or failure;
grasping the wrong object remains a semantic failure. Empty event lists are valid.

The next-run prompt is `scripts/annotate/prompts/semantic_coverage_v2/progress_failure.md`.
The separately authorized [semantic rerun](frame_selection_semantic_v2.md) uses
this richer revision. Selector and subset instructions are unchanged. Future runs must preflight output headroom for
the richer format within the spending cap; do not silently truncate or change
generation settings on only some arms.
The separately authorized [full-coverage rerun](frame_selection_full_coverage.md)
used `full_coverage_v1` with the same four binary states and coarser segmentation.
Earlier experiments used positive intervals with optional
uncertain intervals. Their gaps must not be
converted to no/no automatically; completing those annotations requires review or
a newly authorized annotation run. Frozen model responses remain unchanged.
