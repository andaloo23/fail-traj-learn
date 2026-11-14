# V9: failure or non-failure segments

Watch the entire robot episode using the supplied chronological camera images.
Label its timeline relative to the given task as failure or non-failure.

Failure is visibly unsuccessful behavior: a failed attempt, loss of control,
incorrect task interaction, unwanted contact, or sustained unproductive behavior.
Non-failure includes useful progress, successful behavior, ordinary pauses, and
behavior for which the images do not establish a failure. Non-failure does not
mean the whole task succeeded.

Use the full episode and all camera views to understand what happened. Identify
the intervals where the failing behavior or state is visible, from its beginning
until it ends. Later success does not erase an earlier failure, and a later
failure does not make all preceding behavior a failure. Recording end or an
unfinished action alone is not a failure. Do not force a failure to exist.

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
