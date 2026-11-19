# Episode: C0906

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left stuffed toy is white and blue, and the largest bowl is the central white bowl. The robot instead lifts the pink toy from the right foreground (frames 24–28) and releases it into the white bowl (frames 40–41). At frame 99, the intended blue toy remains on the table; this is a visible wrong-object execution, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 11 | No |
| 11 | 42 | Yes |
| 42 | 61 | No |
| 61 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 11-42
- Categories: sequencing_semantic
- Explanation: In image_primary frame 11, the gripper is descending toward the right-hand pink toy rather than the left-hand blue toy. It acquires and lifts the pink toy in frames 21–28, then deposits it into the largest white bowl in frames 40–41. Physical handling succeeds, but moving the wrong toy does not fulfill the task.
- Recovery: Return the pink toy to its original table location, then acquire the left white-and-blue toy and place it into the white bowl. No human intervention appears necessary.
- Severity: low
- Severity evidence: The wrong toy is relocated into an upright bowl; image_primary frame 41 shows no visible damage, spill, or meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: Restoring the original scene requires a straightforward relocation of the pink toy from the accessible bowl to the table; no repair or difficult retrieval is indicated.

### Failure 2

- Frames: 61-100
- Categories: task_not_attempted
- Explanation: In image_primary frames 61–99, the empty gripper remains near the white bowl with only small positional changes for roughly eight seconds. It makes no discernible approach to the intended blue toy, which remains untouched on the left. This sustained inactivity does not advance the still-unfinished task.
- Recovery: Resume task-directed movement toward the left white-and-blue toy, grasp it, and place it in the largest white bowl; also correct the earlier wrong-object relocation. No human intervention is visibly required.
- Severity: low
- Severity evidence: The stalled interval leaves the task incomplete but causes no additional visible damage or disruption in image_primary frames 61–99.
- Resetability: immediate
- Resetability evidence: The stall itself creates no environmental change requiring reset; the robot can resume from its current pose. The earlier pink-toy relocation is assessed separately.
