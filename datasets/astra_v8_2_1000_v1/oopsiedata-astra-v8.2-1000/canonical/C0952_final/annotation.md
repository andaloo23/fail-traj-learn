# Episode: C0952

## Episode annotation

- Language task: Pick up the teal block and stack it on top of the green block.
- Success label: failure
- Outcome evidence: The robot eventually lifts and transports the teal block toward the green block (frames 185–199, wrist_cam and right_base_cam), but the released teal block tips off and settles beside the green block (frames 200–208, wrist_cam). Both blocks remain separate at frame 240 in wrist_cam and left_base_cam. This is a visibly failed stacking attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 41 | No |
| 41 | 184 | Yes |
| 184 | 200 | No |
| 200 | 208 | Yes |
| 208 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 41-184
- Categories: task_not_attempted
- Explanation: After reaching the teal block, the robot spends an extended interval hovering with small back-and-forth adjustments and gripper movements without lifting or transporting it; compare frames 41, 81, 112, 150 and 183 in wrist_cam and right_base_cam. This sustained lack of progress is distinct from the initial approach; the images do not establish a mechanical fault or individual completed failed grasps.
- Recovery: Reassess the teal block's position, align the fingers around suitable opposing surfaces, close the gripper and verify possession with a small lift before transporting it; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The delay prevents progress, but no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The blocks remain accessible on the table and no environmental intervention is needed to resume acquisition.

### Failure 2

- Frames: 200-208
- Categories: manipulation
- Explanation: Following established transport of the teal block, the gripper opens near the green block at frame 200; the teal block tilts and falls aside through frames 201–207 rather than remaining stacked, as shown in wrist_cam and corroborated by right_base_cam. By frame 208 the blocks are separate on the table. The visible failure is unstable placement, without evidence of a hidden cause.
- Recovery: Reacquire the teal block from its new pose, align its supporting surface securely over the green block, lower it into stable contact and release only after checking support; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The teal block falls a short distance onto the tabletop; no damage is visible and both task objects remain usable.
- Resetability: immediate
- Resetability evidence: Both blocks remain within the accessible workspace, so the robot can reattempt stacking without a human reset.