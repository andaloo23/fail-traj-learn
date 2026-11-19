# Episode: C0161

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 399 in image and left_ego_image. The robot moves toward the oven’s upper front area during frames 0–99, but then remains essentially stationary through frame 399; wrist_image also shows no subsequent handle acquisition or door-opening motion. Completion is not observed, and sustained stalling is visible rather than a confirmed failed grasp or pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 100 | No |
| 100 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 100-400
- Categories: task_not_attempted
- Explanation: Following the initial approach and small adjustments, the gripper stays essentially fixed near the oven without visibly opening it for approximately 25 seconds. Frames 100, 200, 300 and 399 in image, left_ego_image and wrist_image show the unchanged gripper configuration and closed door. This sustained lack of progress establishes stalling; the images do not establish a secure handle grasp or a hidden cause.
- Recovery: Reassess the handle position, align the gripper for a secure acquisition, and then open the door along its hinge motion while monitoring clearance. No environmental human intervention is visibly needed.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible during the stall.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; another task-directed attempt requires no visible environmental reset.