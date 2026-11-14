# V9.1: failure or non-failure segments

Watch the entire robot episode using the supplied chronological camera images.
Judge the robot's behavior relative to the given language task.

Failure: Yes means a continuous period of visibly unsuccessful, task-inconsistent,
or persistently unproductive behavior that does not advance the task. Include
observable failed attempts and unintended side effects even if the episode
eventually succeeds.

Failure: No includes ordinary task-directed behavior, useful progress, successful
behavior, and brief ordinary pauses. No immediate object movement does not by
itself mean failure: approaching, aligning, and preparing can advance the task.
Use No when the images do not establish failure; this does not certify success.

## Failure recognition criteria

These criteria define the binary judgment; they are not additional output labels.

- Reaching: the robot misses the required object or interaction position without
  making contact. A near-object grasp miss belongs to grasping instead.
- Grasping: the robot fails to acquire or retain control of the object, including
  a missed or incorrect grasp, slipping, or dropping.
- Manipulation: control is established but the intended interaction fails, such
  as grasping a handle without opening the door or placing an object outside its
  intended destination.
- Sequencing or semantic: the robot visibly engages the wrong object, performs
  the wrong operation, or follows an incorrect task sequence. Do not infer hidden
  planning or perception errors.
- Collision: unwanted contact with obstacles or the environment, including
  bumping or knocking over unrelated objects. Required task contact is not a
  collision failure.
- Task not attempted: no discernible task attempt or clear sustained stalling.
  A short pause or slow but task-directed movement alone is not sufficient.
- Abnormal termination: a visible abnormal interruption cuts execution short.
  The video file ending, including during an ongoing action, is not sufficient.
- Visible mechanical issue: an observable robot malfunction prevents appropriate
  execution. Do not invent a fault from an unsuccessful action alone.
- Other: another visibly unsuccessful or task-disrupting behavior not covered
  above.

## Decision rules

- Fingers still closing, with acquisition not yet established: an unfinished
  attempt alone is not failure.
- The gripper completes an acquisition attempt and clearly moves away empty
  while the target remains behind: this establishes failed acquisition.
- The robot briefly pauses and then continues the task: do not label the pause
  as stalling merely because progress was temporarily absent.
- The recording ends while an action is still underway: do not label failure
  solely because its outcome is not shown.
- Use before/after observations and all views to resolve what happened. A later
  success does not erase earlier failure; a later failure does not make all
  preceding behavior a failure. Do not force a failure to exist.

## Segment boundaries

Start a failure segment at the earliest moment the failing behavior is observable,
not automatically at the beginning of an attempt because its later outcome is bad.
End it when the robot resumes task-progressing behavior or recovery, or at the end
of the episode if no such recovery is observed. Label the observable failing
interval, rather than only the instant its outcome is confirmed. Do not extend
failure through subsequent good behavior merely because its consequences persist.

Continuous bad behavior forms one Yes segment. Bad behavior separated by good
behavior forms separate Yes segments. Because the output is binary, merge adjacent
Yes segments even if the failure type changes. Do not split solely because the
robot changes actions.

Partition every source frame into contiguous, non-overlapping segments. Use
original frame indices: start inclusive, end exclusive, beginning at 0 and ending
at the supplied source frame count. Merge adjacent segments with the same label.

Return only this Markdown format, replacing the placeholders. Failure is Yes or
No. Include no explanations, action names, failure categories, evidence lists,
confidence fields, or other text.

# Episode: EPISODE_ID

| Start frame | End frame | Failure |
| --- | --- | --- |
| START | END | Yes or No |
