# Episode: C0340

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed at frame 4 in image and left_ego_image. The robot approaches the oven during frames 29–96, but no opening is visible. Frames 100, 160 and 222 in image, left_ego_image and wrist_image show essentially the same gripper position beside the still-closed oven. Completion is not confirmed; the visible local failure is sustained stalling, not an established failed grasp or pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 100 | No |
| 100 | 223 | Yes |

## Failure annotations

### Failure 1

- Frames: 100-223
- Categories: task_not_attempted
- Explanation: After approaching the oven, the robot remains essentially stationary beside it throughout frames 100–222, with no discernible acquisition, pull or door movement. Comparing frames 100, 160 and 222 in image, left_ego_image and wrist_image establishes sustained unproductive behavior while the door remains closed; the cause of the stall is not visible.
- Recovery: Reassess the handle position, align the gripper for a secure acquisition, and then open the door along its hinge path while monitoring clearance. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible in image and left_ego_image through frame 222.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their existing usable positions; another attempt can begin without environmental resetting or visible need for human intervention.