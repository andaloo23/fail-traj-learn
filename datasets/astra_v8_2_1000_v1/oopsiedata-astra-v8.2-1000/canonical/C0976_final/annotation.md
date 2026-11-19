# Episode: C0976

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 298 in left_ego_image. The robot raises and repositions its gripper toward the handle, with closer alignment visible in wrist_image at frames 151–203, but no door-opening motion is visible. Completion is unconfirmed rather than a clearly demonstrated failed pull; a sustained pause during the approach is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 33 | No |
| 33 | 96 | Yes |
| 96 | 299 | No |

## Failure annotations

### Failure 1

- Frames: 33-96
- Categories: task_not_attempted
- Explanation: After the initial upward approach, the gripper remains essentially stationary above and beside the closed oven for approximately five seconds, without acquiring the handle or opening the door; compare frames 33, 60, and 95 in image, left_ego_image, and wrist_image. This sustained pause makes no discernible task progress; its underlying cause is not visible.
- Recovery: Resume a controlled approach to the oven handle, align the fingers around it, establish a secure grasp, and pull along the door's opening direction; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The pause delays the task, but no damage, object displacement, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain unchanged, so the robot can continue the attempt without environmental resetting or human intervention.