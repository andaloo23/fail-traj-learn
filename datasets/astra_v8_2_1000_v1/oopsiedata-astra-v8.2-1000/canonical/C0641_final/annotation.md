# Episode: C0641

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is blue-and-white and the largest bowl is the central white bowl. The robot instead handles the pink toy on the right, placing it in the white bowl by frames 43–44. The intended blue-and-white toy remains on the table through frame 99. This is a visibly wrong-object attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 8 | No |
| 8 | 44 | Yes |
| 44 | 61 | No |
| 61 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 8-44
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary frames 8–17, the gripper targets and closes around the right pink toy rather than the left blue-and-white toy. It withdraws empty in frames 18–20 while the pink toy remains on the table, establishing a failed acquisition. It then retries, lifts the pink toy in frames 30–33, and deposits it in the largest white bowl in frames 41–43. The continuous wrong-object handling does not accomplish the requested transfer.
- Recovery: Return the pink toy to its original table location, then acquire the left blue-and-white toy and place it in the white bowl; no human intervention appears necessary.
- Severity: low
- Severity evidence: The wrong toy is slightly displaced and then relocated into a bowl; no damage or meaningful damage risk is visible in image_primary frames 17–44.
- Resetability: minor_reset
- Resetability evidence: Restoring the pink toy from the accessible white bowl to the table is a straightforward reset; no repair or difficult retrieval is indicated.

### Failure 2

- Frames: 61-100
- Categories: task_not_attempted
- Explanation: Following withdrawal from the bowl, the robot remains essentially stationary in image_primary frames 61–99, with the left blue-and-white toy still untouched on the table. This sustained inactivity does not advance the still-uncompleted task.
- Recovery: Resume task-directed movement, identify the left blue-and-white toy, and transfer it into the largest white bowl after correcting the earlier wrong-object placement; no human intervention appears necessary.
- Severity: low
- Severity evidence: The inactivity delays completion but produces no additional visible displacement, damage, or damage risk.
- Resetability: immediate
- Resetability evidence: The stall itself changes no environmental state, so movement can resume without a reset; the earlier wrong-object placement is assessed separately.
