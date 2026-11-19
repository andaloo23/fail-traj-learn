# Episode: C0971

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is blue and white, and the largest bowl is the central white bowl. The robot instead picks up the right pink toy (frames 14–22) and deposits it in that bowl (frame 39). At frame 99, the blue-and-white toy remains on the table and the pink toy remains in the bowl; this is a visibly wrong-object execution, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 7 | No |
| 7 | 43 | Yes |
| 43 | 82 | Yes |
| 82 | 100 | No |

## Failure annotations

### Failure 1

- Frames: 7-43
- Categories: sequencing_semantic
- Explanation: In image_primary, the gripper visibly approaches the right pink toy at frames 7–10, acquires and lifts it at frames 14–22, and releases it into the largest white bowl at frame 39. The left blue-and-white toy remains untouched. The physical transfer succeeds, but it moves the wrong object.
- Recovery: Return the pink toy to its original table location, then acquire the left blue-and-white toy and place it in the white bowl; no human intervention appears necessary.
- Severity: low
- Severity evidence: The wrong soft toy is relocated into an intact bowl; image_primary frames 39–43 show no visible damage or meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: Restoring the original scene requires a straightforward relocation of the pink toy from the accessible bowl to the table, with no repair or difficult retrieval.

### Failure 2

- Frames: 43-82
- Categories: task_not_attempted
- Explanation: After releasing the wrong toy, the robot remains hovering over the white bowl with only small positional changes throughout image_primary frames 43–81. This sustained interval makes no progress toward moving the still-visible left toy; clearer upward withdrawal begins at frame 82.
- Recovery: Re-identify the left blue-and-white toy and resume a task-directed approach, correcting the wrong-object placement first; no human intervention appears necessary.
- Severity: low
- Severity evidence: The sustained hovering wastes time but causes no additional visible object displacement or damage in image_primary frames 43–81.
- Resetability: immediate
- Resetability evidence: The hovering itself creates no additional environmental reset requirement; the robot can immediately resume task-directed action, independently of correcting the preceding wrong-object placement.