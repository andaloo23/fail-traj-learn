# Annotate progress and failure from visible evidence

Identify supported progress and failure intervals relative to the episode's language
task. Use only the supplied synchronized camera images and ordinary robot telemetry.
Progress and failure are independent labels and may overlap. The episode may have
no failure segments. Do not assume either success or failure in advance.

## Establish identity before assigning task progress

Separate the object requested by the task from the object the robot actually touches
or carries. The instruction describes the goal; it does not identify whatever is
inside the gripper. Track the manipulated object's appearance and location across
both cameras. Inspect available views before contact, during transport, and after
placement for readable packaging, shape, markings, and other distinguishing evidence.

State whether the manipulated object matches the requested object: supported match,
supported mismatch, or unresolved. Cite source frames and camera views. Quote package
text only when it is actually legible; never complete blurry text from the task or
from expectations. Color alone may not distinguish similar packages. Reconcile
conflicting views rather than naming the object from its first appearance. If the
requested object cannot be located, that alone does not prove the carried object
is wrong. A clear identity mismatch can establish a wrong-object action without
locating the requested object elsewhere.

Do not let uncertainty about identity erase directly visible physical failures.
When identity remains unresolved, mark affected task-level judgments uncertain
instead of confidently declaring either a correct-object or wrong-object action.

## Label the task effect and physical behavior separately

**Progress:** observable advancement toward the requested task, including a productive
approach or correction. Successful motion, grasping, or transport of an object is
not automatically progress: it must advance the specified object/action/destination.
A wrong-object action is not progress merely because it resembles the requested action.

**Failure:** an observable unsuccessful attempt, task-inconsistent action, harmful
side effect, or sustained unproductive behavior. Absence of immediate progress alone
is not failure. Productive action with a harmful side effect may receive both labels.
A successful episode may contain failures. A brief pause or recording end alone
does not establish stalling, task failure, or sudden termination.

For each apparent grasp, loss, or release, check before/after object motion in both
cameras. A close/open command, finger aperture, or end-effector motion does not prove
contact, possession, or separation. Occlusion is not evidence that an object was
dropped. Remaining near the gripper does not by itself prove attachment. Distinguish
support by a surface from being carried. Report uncertainty where these alternatives
cannot be resolved; do not invent sticking, damage, or hidden planning faults.

Keep the instructed identity, physical observations, and interval labels consistent
throughout the answer. Check the later visible evidence against the initial identity
claim. Also check for missed attempts, wrong-object interactions, release problems,
and side effects; do not force any of these to exist. Provide concise evidence-based
conclusions, not a speculative account of internal robot decisions.

## Failure categories

Choose all supported categories for each failure interval:

- Reaching: pre-contact failure to reach the target object/location.
- Grasp: missed/improper grasp, slip, or drop; a barely missed grasp belongs here.
- Manipulation: post-contact failure to manipulate as intended.
- Sequencing or semantic: wrong object, action, destination, or order.
- Collision: observed collision with an obstacle/environment.
- Task not attempted: no discernible attempt, including sustained stalling.
- Visible hardware/mechanical issue: a visibly supported mechanical problem.
- Other: describe the observable issue.

## Boundaries and uncertainty

Use source-frame indices at the supplied FPS. All intervals are half-open [start, end):
start inclusive, end exclusive, with 0 <= start < end <= n_frames. The exclusive end
may equal n_frames; do not cite that boundary as an observed image.

Merge continuous behavior within each label; split when that behavior stops. A change
in category alone need not split continuous failure. Explain when different categories
apply within a merged interval. Do not extend a physical failure to an entire semantic
failure interval without evidence. Productive correction is progress, not a separate
recovery class. There is no neutral class; unlabeled gaps are not verified negatives.

Start a failure when the erroneous behavior is first supported by observable evidence.
Do not backdate a wrong-object failure to an ambiguous initial approach solely because
the later grasp is wrong. Boundaries between samples may be estimated, but describe
their uncertainty. Cite only supplied source frames and camera views. Commands at
frame t follow observation t. No recovery advice, severity, resetability, or terminal
outcome classification is requested.

## Return Markdown

Return ordinary Markdown, without JSON or a surrounding code fence. Start with the
episode ID and task. Use exactly these level-two sections:

## Object identity check

Briefly report the requested object, manipulated object, match/mismatch/unresolved,
and the supporting frame numbers and camera views. Distinguish readable identifying
features from guesses. Do not list imagined objects or observations.

## Progress segments

## Failure segments

Under each, give every segment a `###` descriptive heading and these bullets:
- Interval: [start, end), with corresponding times in seconds.
- Description: what visibly happened and why it counts for this task.
- Evidence: supplied source-frame numbers and camera views.
- Uncertainty: material uncertainty in interpretation or timing, or none supported.
- Categories: applicable failure categories (failure segments only).

## Uncertain intervals

Use the same segment heading and Interval bullet. Name the affected label or category
and the missing/conflicting evidence. An uncertain label/category must not also be
asserted confidently over the same interval. Uncertainty about an additional physical
failure can coexist with an independently supported semantic failure; state that scope.

## Limitations

Briefly state evidence limitations. If any segment section is empty, explicitly say
no supported segments; do not invent events to fill it. Intervals within each positive
label must not overlap; progress and failure may overlap each other. Do not force
complete positive coverage. Keep the answer concise enough to finish within its budget.
