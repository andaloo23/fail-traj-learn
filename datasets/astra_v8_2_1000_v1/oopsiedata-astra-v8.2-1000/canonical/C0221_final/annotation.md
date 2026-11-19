# Episode: C0221

## Episode annotation

- Language task: set the mushroom on the green cloth
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot grasps and lifts the mushroom in frames 17–22 and carries it toward the green cloth in frames 23–29. It then spends an extended interval hovering with small repeated movements rather than placing it. Frames 59–69 show further orientation and positioning, but at frame 69 the mushroom remains in the gripper above the cloth. Completion is unconfirmed, not a visibly failed release; no drop or damage is observed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 29 | No |
| 29 | 59 | Yes |
| 59 | 70 | No |

## Failure annotations

### Failure 1

- Frames: 29-59
- Categories: task_not_attempted
- Explanation: In right_shoulder_cam frames 29–58, the robot holds the mushroom above the cloth area with repeated small vertical and lateral movements, without sustained progress toward lowering or releasing it. This extended hovering constitutes stalling after successful acquisition, rather than a failed grasp. A distinct orientation adjustment begins at frame 59.
- Recovery: Maintain the grasp, align the mushroom over the cloth, lower it until supported, and release before withdrawing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The delay prevents task completion during this interval, but the mushroom remains held and no damage, dropping, or harmful contact is visible.
- Resetability: immediate
- Resetability evidence: The cloth and surrounding objects remain undisturbed, and the robot can continue placement from its current grasp without an environmental reset.