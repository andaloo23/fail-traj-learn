# Episode: C0567

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed at frame 0 in left_ego_image and remains visibly closed during the approach at frames 150 and 200. The robot subsequently positions its gripper near the oven handle, but no door opening is visible through frame 311 in image and left_ego_image; wrist_image provides a close but partially occluded view. Completion is unconfirmed rather than a conclusively completed, failed pulling attempt. A sustained earlier pause is observable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 28 | No |
| 28 | 110 | Yes |
| 110 | 312 | No |

## Failure annotations

### Failure 1

- Frames: 28-110
- Categories: task_not_attempted
- Explanation: Following the initial repositioning, the robot remains nearly stationary above and beside the closed oven for approximately seven seconds, without acquiring the handle or moving the door. Frames 28, 60, 85, and 109 in image, left_ego_image, and wrist_image show essentially the same gripper placement and closed door. This sustained pause does not visibly advance the task; its underlying cause is unknown.
- Recovery: Resume a controlled approach, align the fingers around the oven handle, verify acquisition, and pull along the door's opening path; no human intervention is visibly required.
- Severity: low
- Severity evidence: The pause delays the attempt but causes no visible damage, displacement, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so the robot can continue the attempt without environmental resetting or human intervention.