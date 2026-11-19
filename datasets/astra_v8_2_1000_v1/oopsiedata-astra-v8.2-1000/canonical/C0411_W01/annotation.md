# Episode: C0411_W01

## Episode annotation

- Language task: put the red banana clip into the green bowl
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window: the red clip/lead remains on the table to the right of the towel and the green bowl remains empty in top at frames 0, 235, and 349, corroborated by right and left. After prolonged initial inactivity, the robot makes small positioning movements beginning around frame 235, but no acquisition or placement is visible. This is a provisional window outcome; later episode context is absent, and no failed grasp is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 235 | Yes |
| 235 | 350 | No |

## Failure annotations

### Failure 1

- Frames: 0-235
- Categories: task_not_attempted
- Explanation: Across frames 0-234, left, right, and top show essentially unchanged gripper positions and untouched objects for approximately 7.8 seconds, with no discernible approach or acquisition. This sustained inactivity does not advance the task; its cause is not visible. Positioning movement becomes apparent at frame 235.
- Recovery: Begin a controlled approach to the red clip, align the gripper, acquire it, and transfer it into the green bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The observed consequence is delay only; no object displacement, damage, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The bowl and target remain in their original usable positions, so task execution can resume without an environmental reset.