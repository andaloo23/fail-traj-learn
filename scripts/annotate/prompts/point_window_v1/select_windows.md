# Select evidence for an independent annotator

Use the task, synchronized external/wrist candidate images, their source timestamps,
and ordinary telemetry to preserve evidence for another model. That model, not you,
will assign progress/failure labels, failure reasons and final segment boundaries.
Return only the requested selections. Do not output labels, object identities,
explanations or reasoning. Do not modify images or invent observations.

Prioritize complementary evidence of object identity and informative temporal changes:
approach/alignment, acquisition, transport, placement, release, loss of control and
meaningful corrections where visible. Preserve before/after views rather than only
a single apparent contact pose. Retain readable distinguishing markings and geometry,
persistent behavior and nearby-object changes; do not select only good or bad moments.
Use both cameras to handle occlusion. The task is a goal, not proof of what happened;
commands and aperture do not establish possession or contact. Do not infer blurry text.

GPT always also receives the fixed overview frames listed in the request. Allocate
the remaining evidence budget to useful details beyond that overview. No human labels
or prior annotations are available. Review the whole candidate sequence before selecting.

## Window selection contract

Select exactly the Window count. Each inclusive window is [start, start+10], spanning
0.5 seconds at 20 FPS. Starts must be from Allowed window starts. List windows in
increasing order with no overlap (a window's end must be strictly before the next start).
Choose windows to bracket informative transitions/ambiguous interactions so GPT can
inspect dense before/after evidence. These are inspection windows, not event or final
segment boundaries. Do not assume an event happens at the window center.

The local program samples the stated pairs per window evenly from original source
frames, including frames you have not seen. If a sample duplicates an overview frame,
it uses the nearest unused frame inside the same window (ties choose the earlier).
It never adds frames outside your windows. Consider coverage and distinguishing
identity evidence as well as brief changes; avoid redundant windows of one interaction.

Return exactly:
# Window selection
## Selected windows
- [start, end]

One inclusive window bullet per selection, without a code fence or extra text.
