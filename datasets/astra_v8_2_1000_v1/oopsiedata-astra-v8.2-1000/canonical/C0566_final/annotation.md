# Episode: C0566

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in left_ego_image at frames 0, 53 and 116. The robot moves toward the oven during the earlier frames, but then remains nearly stationary without visibly opening it; image and wrist_image corroborate the lack of subsequent task progress. Completion is not observed, and the sustained final stall is visible; a failed handle grasp or pull is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 53 | No |
| 53 | 117 | Yes |

## Failure annotations

### Failure 1

- Frames: 53-117
- Categories: task_not_attempted
- Explanation: Following the approach, the robot remains nearly stationary near the oven through frames 53–116, with no discernible handle acquisition or door-opening motion. left_ego_image shows the door remaining closed, while image and wrist_image show no meaningful progress during this sustained interval.
- Recovery: Reassess the handle position, align the gripper, acquire the handle and open the door along its hinge motion while maintaining clearance from the tabletop objects; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible in frames 53–116.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their existing usable state; another task-directed attempt requires no visible environmental reset.