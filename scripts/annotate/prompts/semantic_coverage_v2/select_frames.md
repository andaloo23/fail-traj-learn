# Select a compact visual record

Select timestamps for a later independent annotator. Your only output is source-frame
indices. Do not output object names, identity decisions, progress/failure labels,
diagnoses, summaries, recovery advice, or reasoning. Do not modify any image.

The input provides the task, synchronized external/wrist camera pairs, source-frame
indices, and ordinary robot telemetry. Select exactly K distinct indices from the
candidate list, including every mandatory anchor. Each index retains both original
camera images. The local program will copy the originals; no extra views, crops,
replacement images, or resolution changes are allowed.

Choose complementary evidence for both object identity and temporal interactions:

- Retain clear views that let the later viewer distinguish the task's requested
  object from the object actually handled. Do not assume they are the same object.
  Favor readable packaging/markings and distinctive geometry where visible, including
  wrist views during or after handling if they reveal more than the initial view.
  Do not infer unreadable text or replace visual evidence with a semantic answer.
- Preserve scene context around the approach, before/after attempted pickup,
  transport, placement/release, and the final visible object state where present.
  Include views showing relative motion, separation, or support; a single image
  of proximity cannot resolve these relationships.
- Preserve before/after views of informative changes when the budget permits.
  Include useful views from different phases rather than filling the budget with
  near-duplicates, even if one phase has clearer imagery.
- Preserve representative views of persistent behavior as well as motion, and
  visible changes involving nearby objects. Do not select only apparently good
  moments, only apparently bad moments, or only moments of command changes.
- Use each camera to compensate for occlusion in the other. Keep chronological
  coverage while choosing informative non-anchor frames within the fixed budget.

The task guides which visual details need to remain available; it is not evidence
of what actually happened. Commands and aperture do not establish identity, contact,
or possession. Use only this request, without prior annotations or external sources.
Before returning, verify exact count K, uniqueness, candidate membership, increasing
order, and inclusion of every anchor. Do not add or request more frames.

Return exactly this Markdown structure: a `# Frame selection` heading, a
`## Selected frames` subheading, then one bullet containing only a source-frame
integer for each selected timestamp. No explanations, extra timestamps, JSON, or
code fence. Use only this episode's supplied source-frame indices.
