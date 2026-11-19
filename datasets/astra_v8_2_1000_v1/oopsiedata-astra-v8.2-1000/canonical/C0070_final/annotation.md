# Episode: C0070

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary, frame 0 shows the left blue-and-white toy and the largest, central white bowl. The left toy remains on the table through frame 99. Instead, the robot contacts the right pink toy at frames 42–54 and later lifts it at frames 86–99. This visibly establishes wrong-object handling; placement into a bowl is not confirmed before the recording ends.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 9 | No |
| 9 | 37 | Yes |
| 37 | 55 | Yes |
| 55 | 69 | No |
| 69 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 9-37
- Categories: task_not_attempted
- Explanation: In image_primary, frames 9–36 show prolonged hovering and repeated small back-and-forth movements in front of the white bowl, without reaching or acquiring the left toy. Across this interval, the movements do not produce discernible progress toward acquisition.
- Recovery: Move the open gripper toward the blue-and-white left toy and align around its body before closing; no human intervention is needed.
- Severity: low
- Severity evidence: Both toys and all bowls remain intact and in place; the visible consequence is lost task progress.
- Resetability: immediate
- Resetability evidence: No environmental change needs undoing before a task-directed attempt.

### Failure 2

- Frames: 37-55
- Categories: sequencing_semantic
- Explanation: In image_primary, frames 37–41 show the gripper moving toward the right pink toy rather than the left blue-and-white toy. At frames 42–54 it contacts and shifts the pink toy slightly while leaving the intended toy untouched. Possession is not established during this interval.
- Recovery: Withdraw from the pink toy and redirect acquisition to the left blue-and-white toy; no human intervention is needed.
- Severity: low
- Severity evidence: The unrelated soft toy is slightly repositioned on the tabletop, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The intended toy and destination remain accessible, and the pink toy's small displacement does not prevent another attempt.

### Failure 3

- Frames: 69-100
- Categories: sequencing_semantic
- Explanation: After moving back toward the left toy at frames 55–61, the robot returns to the right pink toy at frame 69 in image_primary. It closes around that toy at frames 73–85 and visibly lifts and carries it at frames 86–99. This is successful acquisition of the wrong object, not evidence of a physical grasp failure; the left toy remains on the table.
- Recovery: Lower and release the pink toy safely onto a clear tabletop area, then acquire the left blue-and-white toy and transfer it into the largest white bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The wrong soft toy is lifted, but no damage, spill, or damaging collision is visible.
- Resetability: minor_reset
- Resetability evidence: The pink toy must be safely returned to the tabletop to restore the scene for a fresh attempt; this is a straightforward reset that the robot could perform.