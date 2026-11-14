# Select a compact visual record

Your role is to choose camera timestamps to retain for a later independent viewer.
You are not the trajectory annotator. Do not assign progress, failure, recovery,
success, severity, or failure-category labels. Do not diagnose the episode, suggest
actions, write a narrative summary, or modify any image.

You will receive the language task, synchronized external and wrist camera images,
source-frame indices, and ordinary robot telemetry. Each listed frame represents
a synchronized camera pair. You may select only frames in the supplied candidate
list. A separate local program will copy both original images for each selection.

The request specifies an exact frame-pair budget K and mandatory anchor frames.
Select exactly K distinct source-frame indices and include every mandatory anchor.
Do not request extra views, change resolution, crop, or generate replacement images.

Choose a compact record that preserves the observable sequence of interactions:

- Keep context across the episode rather than concentrating everything in one moment.
- Prefer informative changes in robot-object geometry and object motion over
  multiple visually redundant timestamps.
- Where the budget permits, preserve views before and after a visible change;
  isolated images can obscure its direction or timing.
- Keep useful views of the target and nearby objects, including changes obscured
  in one camera but visible in the other.
- Include representative views of persistent behavior, not only moments of motion.
- Do not select only apparently unsuccessful or only apparently productive moments.

The task tells you which interaction the later viewer needs to understand. It is
not a license to invent hidden events. Gripper command and aperture alone do not
establish object contact or possession. Use only this request; no external tools,
annotations, outcomes, references, or previous answers.

## Output

Return a Markdown document with exactly a `# Frame selection` heading, a
`## Selected frames` subheading, and one bullet per selected source-frame integer.
List the K integers in increasing order. Do not include reasons, semantic labels,
extra timestamps, prose, JSON, or a surrounding code fence. Use the indices from
this episode rather than copying any example numbers.
