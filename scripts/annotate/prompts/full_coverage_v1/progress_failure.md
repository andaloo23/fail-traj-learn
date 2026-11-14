# Label the entire episode: progress and failure

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
Create a boundary when either judgment changes. Merge adjacent equivalent behavior
where reasonable; do not make a segment merely because another sampled image appears.

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

## Markdown output

Return ordinary Markdown, without JSON or an enclosing code fence. Start with the
episode ID and task, then use these sections:

## Object identity check

Briefly state requested and manipulated identities, match/mismatch/unresolved, and
the cited frame/view evidence or uncertainty. Do not invent identifying observations.

## Segments

Give each segment a `###` descriptive heading and these explicit bullets:
- Interval: [start, end), followed by corresponding times in seconds.
- Progress: yes or no
- Failure: yes or no
- Progress confidence: high, medium, or low
- Failure confidence: high, medium, or low
- Review required: yes or no
- Description: visible behavior and why the chosen pair applies to the task.
- Evidence: actual supplied source-frame indices and camera views.
- Uncertainty: affected judgment/boundary and limitations, or none supported.
- Categories: applicable failure categories, or none.

## Limitations

Briefly state evidence limitations. Before returning, verify exact full coverage,
explicit values for both judgments on every segment, and review flags for uncertain
judgments. Do not omit no/no periods or use silence to represent them.
