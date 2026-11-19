# Episode: C0664

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is white and blue, and the largest bowl is the central white bowl. Instead, the robot acquires the pink toy on the right (frames 13–18) and deposits it in the white bowl (frame 29). The blue toy remains unmoved through frame 71. This is a visibly wrong-object execution, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 5 | No |
| 5 | 30 | Yes |
| 30 | 72 | No |

## Failure annotations

### Failure 1

- Frames: 5-30
- Categories: sequencing_semantic
- Explanation: In image_primary frame 5, the gripper's approach is directed toward the right-hand pink toy rather than the left-hand blue toy. It descends around the pink toy in frames 7–15, lifts it in frames 16–20, and releases it into the largest white bowl at frame 29. Physical acquisition and placement succeed, but handling the wrong toy does not fulfill the requested task.
- Recovery: Return the pink toy to its original tabletop location, then acquire the left blue toy and place it in the white bowl. No human intervention appears necessary.
- Severity: low
- Severity evidence: The wrong plush toy is relocated into an intact bowl; image_primary frames 29–71 show no visible damage or meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: Restoring the original scene requires only moving the pink toy from the accessible white bowl back onto the table; no repair or difficult retrieval is indicated.