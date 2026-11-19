# Episode: C0727

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary, frame 0 shows the intended left toy in blue and white and the largest bowl in white. The robot instead acquires the pink toy on the right (frames 28–45) and releases it into the white bowl (frames 63–65). The left toy remains on the table through frame 99. This is a visible wrong-object execution, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 20 | No |
| 20 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 20-100
- Categories: sequencing_semantic
- Explanation: In image_primary, the gripper moves away from the left blue-and-white toy toward the right pink toy starting at frame 20, aligns with and contacts that toy in frames 24–42, and lifts it in frames 43–45. It carries the wrong toy to the largest white bowl and releases it in frames 63–65, then remains above that bowl through frame 99 without returning to the intended toy. The acquisition and placement are physically successful but do not fulfill the specified object selection.
- Recovery: Return the pink toy to its original tabletop location, then acquire the left blue-and-white toy and place it in the largest white bowl. No human intervention appears necessary.
- Severity: low
- Severity evidence: The wrong soft toy is relocated into an upright bowl; no damage or meaningful damage risk is visible in image_primary through frame 99.
- Resetability: minor_reset
- Resetability evidence: Restoring the original scene requires moving the pink toy from the accessible white bowl back to the tabletop; this is a straightforward reset with no visible repair or difficult retrieval required.