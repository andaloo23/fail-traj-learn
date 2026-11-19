# Episode: C0020

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in image and left_ego_image at frames 0, 49, and 101. Early robot repositioning is visible in wrist_image, but no door-opening motion follows; the gripper remains near the oven with little change through the latter part of the episode. Completion is not observed, and sustained lack of progress is visible; the images do not establish a failed handle grasp or an abnormal interruption.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 49 | No |
| 49 | 102 | Yes |

## Failure annotations

### Failure 1

- Frames: 49-102
- Categories: task_not_attempted
- Explanation: Following initial repositioning, the robot remains nearly stationary near the oven without opening it. Frames 49, 65, 85, and 101 in image and left_ego_image show the door unchanged, while wrist_image shows essentially the same gripper position with only small shifts. This sustained interval does not visibly advance the task; whether the handle is securely contacted is unclear.
- Recovery: Reassess the handle position, align the gripper, establish a secure grasp, and pull along the door’s opening path while monitoring clearance. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so another task-directed attempt requires no visible environmental reset.