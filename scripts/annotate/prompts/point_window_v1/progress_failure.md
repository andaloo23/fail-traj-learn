# Label the entire episode: behavior, progress, and failure reasons

Partition the entire episode into consecutive segments relative to its language
task. Every segment must explicitly answer both questions: is there progress, and
is there failure? Use only the supplied images and ordinary robot telemetry.

## Four allowed combinations

- Progress no, failure no: neither advancement toward the task nor an observable
  unsuccessful attempt, task-inconsistent action, or harmful side effect.
- Progress yes, failure no: advancement without simultaneous failure.
- Progress no, failure yes: failure without simultaneous advancement.
- Progress yes, failure yes: advancement and failure together, such as advancing
  the requested manipulation while causing an observed harmful side effect.

Progress includes a productive approach or correction. Movement, grasping, or
transport is not automatically progress: it must advance the specified object,
action and destination. Failure includes visible unsuccessful attempts, wrong
actions, harmful side effects or sustained unproductive behavior. Lack of immediate
progress alone is not failure; a brief ordinary pause may be no/no. A successful
episode can contain failures. There is no separate recovery category.

## Verify identity and physical evidence

Identify the requested object independently from the object the robot manipulates.
The task describes the goal; it does not prove the held object's identity. Track
appearance and relative location across both cameras and across the episode.
Use readable markings and distinctive features. Quote text only if legible; do not
complete blurry lettering from expectations. Color alone may not distinguish objects.
Report supported match, supported mismatch, or unresolved with cited frames/views.
A clearly identified wrong object can establish mismatch even if the requested object
cannot be located. Failure to locate the requested object alone does not prove mismatch.

For apparent grasp, loss, or release, compare before/after relative motion in both
cameras. Commands, aperture and proximity do not prove possession, contact or release.
Occlusion is not evidence of dropping; remaining near the tool does not prove attachment.
Distinguish being carried from resting against a surface. Do not invent damage,
mechanical faults or hidden planning errors. Check that all labels remain consistent
with the cited identity and physical evidence. Do not assume the episode must fail.

## Full temporal coverage

Use half-open source-frame intervals [start, end) at the supplied FPS. Cover every
frame exactly once: first start = 0, each start = previous end, last end = n_frames.
No gaps, overlaps, zero-length intervals, or separate overlapping positive-label lists.
If progress and failure overlap, split at their boundaries and label that overlap yes/yes.
Create a boundary when either judgment changes OR when a meaningful change occurs
in action phase, object/destination, failure reason/type, concurrent failures, or
recovery attempt. The binary pair alone does not determine segmentation. Adjacent
segments may have identical progress/failure values and identical failure types
while representing different behavior that requires its own explanation.

For example, acquiring a wrong object, transporting it, and trying to place it are
three distinct task phases even if each is progress no/failure yes and wrong_action.
If a carried wrong object is also dropped, split at the supported onset of the loss
and retain both wrong_action and lost_control while both apply. When a local physical
issue ends, remove that reason even if the broader wrong-object failure continues.
These are hypothetical examples, not expected events in the supplied episode.

Describe distinct attempts or corrections separately when the evidence supports a
meaningful change in strategy, contact state, or outcome. An uninterrupted repetition
of the same unsuccessful action can stay one segment with the repetition described.
A successful physical grasp of the wrong object is a semantic error, not automatically
a grasp failure. Recovery that advances the task is progress; correction that repeats
or worsens the error remains failure. A past failure does not automatically make a
later pause or withdrawal a failure: evaluate the behavior in each interval.

Before writing, review the complete sequence for approach/alignment, acquisition,
transport, placement/manipulation, release, retries/corrections, and pauses where
visible. Use only phases supported by this episode. Do not collapse a changing
sequence into one long segment merely because its binary labels are constant.
Do not split only to increase segment count, at every supplied frame, or for tiny
motions with no meaningful change. Merge only when behavior, reasons and evidence
remain materially the same. Keep each description concise and specific.

Use actual source timestamps; images may be sparsely or irregularly sampled.
Boundaries between samples are estimates and must be described as such. Start a
failure at the earliest supported erroneous behavior; do not backdate a wrong-object
failure to an ambiguous approach only because a later grasp is wrong. The exclusive
end n_frames is a boundary, not a visible image. Commands at frame t follow observation t.

## Uncertainty without leaving gaps

For every interval assign the best-supported yes/no pair, even if provisional.
Record confidence separately for progress and failure (high, medium, or low).
If either judgment cannot be established from the evidence, mark that judgment low
confidence and Review required: yes, and explain the missing or conflicting evidence.
Do not present this provisional choice as an established fact. Never default to no/no
because frames are missing, identity is unclear, or an event is occluded. Uncertainty
is attached to the segment, not a separate semantic class or an unlabeled interval.

## Failure categories

For failure yes, choose all supported categories: Reaching (pre-contact), Grasp
(including a barely missed grasp, slip or drop), Manipulation (post-contact),
Sequencing or semantic (wrong object/action/destination/order), Collision,
Task not attempted (including sustained stalling), Visible hardware/mechanical issue,
or Other (describe). For failure no, write Categories: none. If the failure judgment
is provisional, identify category uncertainty too. Recording termination alone does
not establish a failure. Do not output severity, resetability or recovery advice.

## Failure reason classification

For every failure segment also assign one or more of the original R-style failure
types: missed_target (an attempted reach/grasp/placement misses its intended target),
lost_control (observed slip, drop or unintended loss of control), wrong_action
(wrong object, action, destination or order), collision (observed unwanted contact),
timeout (supported cutoff or sustained task-level stalling), or other (explain).
Use none when Failure is no. Use unknown only when Failure is provisional and its
type cannot be resolved; mark Review required yes and explain the uncertainty.
Do not turn an ordinary recording endpoint into a timeout. These types complement
the phase-based Categories field; multiple supported reasons may coexist.

State the specific failure reason in ordinary language: what the robot did, what
observable result conflicted with the task, and why the chosen type applies. Name
the affected object/action/destination when supported. "Failed manipulation" alone
is insufficient. Distinguish observations from hypotheses; an apparent missed grasp
does not establish a hidden perception or planning defect. Keep physical execution
and task relevance separate. For non-failure segments write Failure reason: none,
and explain progress or the absence of both labels in Description.

## Key physical events

Restore the original R-style event evidence alongside the segments. Report only
supported grasp/acquisition, release/disengagement, loss of control, and settling
transitions. An event can occur in any of the four segment states: physical success
does not establish task success. Opening/closing commands alone are not events.
For ambiguous loss, state that the mechanism is unresolved; do not fabricate
bilateral contact state. Use a source-frame window bracketing the visible transition,
evidence from actual supplied frames/views, confidence, and a brief reason. Do not
claim exact timing between sparse samples. Empty events are valid.

## Markdown output

Return ordinary Markdown, without JSON or an enclosing code fence. Start with the
episode ID and task, then use these sections:

## Object identity check

Briefly state requested and manipulated identities, match/mismatch/unresolved, and
the cited frame/view evidence or uncertainty. Do not invent identifying observations.

## Episode summary

State the visible episode outcome (success, failure, or unknown), summarize the
observed sequence and remaining ambiguity. A successful outcome can still contain
failure segments or harmful side effects. Do not infer unseen completion.

## Segments

Give each segment a `###` descriptive heading and these explicit bullets:
- Interval: [start, end), followed by corresponding times in seconds.
- Progress: yes or no
- Failure: yes or no
- Progress confidence: high, medium, or low
- Failure confidence: high, medium, or low
- Review required: yes or no
- Phase: concise task-relevant action phase, object, and destination where supported.
- Description: visible behavior and why the chosen pair applies to the task.
- Evidence: actual supplied source-frame indices and camera views.
- Uncertainty: affected judgment/boundary and limitations, or none supported.
- Categories: applicable failure categories, or none.
- Failure types: one or more R-style types from the list above, none, or provisional unknown.
- Failure reason: specific observed error and task consequence, or none.
- Boundary reason: what changed from the preceding segment; write episode start for the first.

## Events

Write none if no physical transition is supported. Otherwise give each event a
`###` descriptive heading and these bullets:
- Type: grasp, release, lost_control, or settled
- Frame window: [earliest, latest] inclusive source-frame indices bounding the event
- Confidence: high, medium, or low
- Evidence: supplied frame indices and camera views supporting the transition
- Reason: observable before/after change, with timing/mechanism uncertainty

## Limitations

Briefly state evidence limitations. Before returning, verify exact full coverage,
explicit values for both judgments on every segment, and review flags for uncertain
judgments. Check that different supported phases/reasons have not been collapsed
under one constant binary pair, that continuing reasons carry forward only while
they apply, and that event windows agree with segment descriptions. Do not omit
no/no periods, invent events to create more segments, or use silence for labels.
