# Episode: C0910

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left stuffed toy is white and turquoise, and the largest bowl is the central white bowl. The robot instead handles the pink toy on the right, leaving it in the white bowl by frame 47. Frames 50–99 show the left toy still on the table and no further task-directed movement. This is visible wrong-object execution, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 7 | No |
| 7 | 50 | Yes |
| 50 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 7-50
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary frame 7, the gripper is aligned around the right pink toy rather than the left white-and-turquoise toy. It closes around the pink toy during frames 14–21 but withdraws empty in frames 23–24 while that toy remains on the table, establishing a failed acquisition. It retries, lifts the pink toy in frames 33–36, and releases it into the largest white bowl at frame 47. The entire sequence targets the wrong object and does not accomplish the requested transfer.
- Recovery: Return the pink toy to its original tabletop area, then acquire the left white-and-turquoise toy and place it in the white bowl, verifying possession and release visually; human intervention is not evidently needed.
- Severity: low
- Severity evidence: The wrong toy is relocated and an acquisition fails, but image_primary frames 23–49 show no visible damage or meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: Restoring the initial scene requires a straightforward transfer of the pink toy from the accessible white bowl back to the table; no repair or difficult retrieval is indicated.

### Failure 2

- Frames: 50-100
- Categories: task_not_attempted
- Explanation: In image_primary frames 50–99, the gripper remains stationary above the white bowl while the requested left toy stays untouched on the table. This sustained inactivity does not advance the still-uncompleted task; the recording end alone does not establish abnormal termination.
- Recovery: Resume task-directed movement, identify the left white-and-turquoise toy, and transfer it to the largest white bowl after correcting the prior wrong-object placement; human intervention is not visibly required.
- Severity: low
- Severity evidence: The sustained inactivity leaves the task incomplete but causes no additional visible damage or disturbance in image_primary frames 50–99.
- Resetability: immediate
- Resetability evidence: This idle interval creates no additional environmental change requiring a reset; the robot can resume, with the earlier wrong-object relocation addressed separately.
