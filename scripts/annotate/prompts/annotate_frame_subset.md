# Annotate from the supplied visual samples

The common progress/failure annotation guide follows this input-handling note.
Apply its definitions, failure categories, Markdown output guidance, and uncertainty
rules unchanged.

The request contains a chronological sequence of synchronized camera pairs, their
original source-frame indices, and ordinary robot telemetry. The visual timestamps
may be unevenly spaced and do not necessarily show every recorded frame. Use the
actual timestamp gaps; do not interpret neighboring supplied images as neighboring
source frames or as a fixed playback rate.

Judge the episode from the supplied evidence. Do not treat inclusion of an image
as evidence that something good or bad happened there. Do not assume a particular
sampling method. No previous annotator's interpretation is supplied.

Distinguish a visible transition from an event inferred across a gap. If the available
images cannot resolve whether progress or failure occurred, or when its interval
starts or ends, state that uncertainty. Do not fill missing visual evidence with a
confident story. Ordinary telemetry is supporting evidence, not proof of grasp,
contact, task completion, or object identity.

Return the same human-readable Markdown annotation described in the common guide.
This is an independent annotation, not a review of another model's answer.
