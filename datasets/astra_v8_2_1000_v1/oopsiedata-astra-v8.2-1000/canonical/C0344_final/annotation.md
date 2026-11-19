# Episode: C0344

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed at frame 0 in left_ego_image. The robot approaches the oven during frames 0–77, but then remains near its upper front area without visibly opening it. At frames 160, 240 and 319, left_ego_image still shows the closed door; image and wrist_image show no successful pulling motion. Completion is not merely obscured or unconfirmed: the door visibly remains closed following prolonged unproductive behavior.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 78 | No |
| 78 | 320 | Yes |

## Failure annotations

### Failure 1

- Frames: 78-320
- Categories: task_not_attempted
- Explanation: After the initial approach, the robot stays near the oven with only small positional changes and no visible door-opening progress throughout frames 78–319. left_ego_image shows the door remaining closed at frames 78, 160, 240 and 319, while wrist_image and image show the largely stationary gripper. This is sustained stalling; the images do not establish a completed failed grasp or a mechanical cause.
- Recovery: Reassess the handle position, align the gripper to acquire it securely, and execute a controlled opening motion while monitoring door movement and clearance. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state, so another attempt needs no environmental reset or human intervention.