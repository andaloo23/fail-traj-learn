# Annotate progress and failure

Identify all supported progress and failure intervals in this robot episode relative
to its language task. Use only the supplied images/video and ordinary robot
telemetry. Progress and failure are independent labels and may overlap.

## Definitions

**Progress:** observable advancement toward the task, including a productive
approach or correction.

**Failure:** an observable unsuccessful attempt, task-inconsistent action, harmful
side effect, or sustained unproductive behavior. Absence of immediate progress
alone is not failure. A successful episode can contain failures. Progress with a
harmful side effect should receive both labels over the overlap. Do not infer
hidden perception/planning faults or damage from insufficient evidence.

Draw separate intervals for progress and failure. Merge continuous behavior within
each label; split when it stops. A category change alone need not split continuous
failure: assign all applicable types. A productive correction is progress, not a
separate recovery class. There is no neutral class. Omission does not mean negative.

## Failure categories

Choose one or more for each failure interval:

- Reaching: pre-contact failure to reach.
- Grasp: missed or improper grasp, slip or drop; a barely missed grasp belongs here.
- Manipulation: post-contact failure to manipulate as intended.
- Sequencing or semantic: wrong object, action or order.
- Collision.
- Task not attempted: no discernible attempt, including sustained stalling.
- Visible hardware/mechanical issue.
- Other: describe the observable issue.

A recording ending is not by itself a failure. Describe observable behavior rather
than inventing its hidden cause.

## Timing and evidence

Use source-frame indices at the supplied source FPS. Report interval starts as
inclusive and ends as exclusive: [start, end). Boundaries may be estimated between
samples, but acknowledge timing uncertainty. Do not claim brief events you cannot
see. Cite actual supplied image frames, or visible timestamps for video; video
timestamps can be converted to source frames using the source FPS.

If evidence is insufficient, describe an uncertain interval and which label is
uncertain. Opening/closing commands and finger positions do not prove grasp or
contact. Commands at frame t follow observation t. Do not include recovery advice,
severity ratings, resetability estimates or terminal-outcome classification.

## Write the annotation in Markdown

Write an ordinary Markdown document, not JSON, and do not wrap the whole document
in a code fence. Start with the episode ID and task.

Use a **Progress segments** section and a **Failure segments** section. Give each
segment a short heading and describe:

- Its source-frame interval [start, end) and corresponding times in seconds.
- What visibly happened and why it counts as progress or failure.
- Supporting frames or video timestamps.
- Any uncertainty about the behavior or boundaries.
- For failure segments, the applicable failure categories.

Use **Uncertain intervals** for behavior that cannot be assigned confidently,
including the interval, affected label(s), and what prevents a decision. End with
brief **Limitations**. If a section has no supported segments, say so explicitly;
do not fill it with invented events.

Positive intervals within the same label must not overlap. Progress and failure
may overlap each other. An uncertain interval must not also be a confident positive
for the same label. Do not force full positive coverage of the episode.
