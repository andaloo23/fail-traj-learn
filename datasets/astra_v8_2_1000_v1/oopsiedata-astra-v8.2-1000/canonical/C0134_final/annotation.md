# Episode: C0134

## Episode annotation

- Language task: stack the yellow block on the blue blocks
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot approaches and closes its fingers near the yellow block at frames 8–27, then lifts away empty at frames 28–33. It subsequently moves above the blue blocks without the yellow block at frames 34–46. At frame 69, the yellow block remains on the table beside the blue blocks; this is a visibly failed acquisition and incomplete stack, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 28 | No |
| 28 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 28-70
- Categories: grasp, sequencing_semantic
- Explanation: In right_shoulder_cam at frames 28–33, the fingers rise empty while the yellow block remains on the table, establishing failed acquisition. Rather than reacquiring it, the robot continues toward and lowers above the blue blocks at frames 34–46 without carrying the yellow block, then withdraws slightly and hovers through frame 69. This empty continuation does not advance the stacking task.
- Recovery: Return to the yellow block, align the open fingers around its opposing sides, acquire it, and verify possession before transporting it above the blue blocks and releasing it onto a stable support. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The yellow block remains on the tabletop and the blue blocks remain undisturbed; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The yellow block is still accessible beside the blue blocks, so another acquisition attempt can begin without environmental resetting or human intervention.