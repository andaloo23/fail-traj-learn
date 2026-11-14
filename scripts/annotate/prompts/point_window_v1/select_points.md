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

## Point selection contract

Select exactly the Additional point count, all distinct and in increasing order,
from the supplied candidate indices, excluding fixed overview indices. Each retains
both original camera views. Choose complementary points that preserve identity and
both sides of important changes. Do not request any frames outside the candidate list.

Return exactly:
# Frame selection
## Selected frames
- integer

One integer bullet per chosen frame, without a code fence or extra text.
