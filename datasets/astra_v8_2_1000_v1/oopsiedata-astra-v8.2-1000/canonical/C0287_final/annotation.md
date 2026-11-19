# Episode: C0287

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left stuffed toy is the blue-and-white toy, and the largest bowl is the central white bowl. Instead, the robot handles the pink-and-brown toy on the right and places it in that bowl by frames 44–46. The intended left toy remains unmoved on the table through frame 76; this is a visible wrong-object attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 6 | No |
| 6 | 50 | Yes |
| 50 | 77 | No |

## Failure annotations

### Failure 1

- Frames: 6-50
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary frames 6–19, the robot targets and closes around the right pink-and-brown toy rather than the left blue-and-white toy. It withdraws empty in frames 20–22 while the pink toy remains on the table, establishing a failed acquisition. It then retries, lifts the wrong toy in frames 33–38, releases it into the largest white bowl in frames 44–46, and withdraws through frame 49. The successful second grasp does not correct the wrong-object selection.
- Recovery: Return the pink-and-brown toy to its original table location, then acquire the left blue-and-white toy and place it in the white bowl. Human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The wrong toy is relocated and the intended task remains undone; image_primary frames 44–76 show no visible damage, spill, or meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: Restoring the original scene requires moving the pink-and-brown toy from the bowl back to the table, a straightforward reset; the bowl and both toys remain accessible and visibly intact.