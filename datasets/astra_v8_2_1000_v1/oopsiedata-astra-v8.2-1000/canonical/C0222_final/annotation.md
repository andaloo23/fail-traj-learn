# Episode: C0222

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 270 in left_ego_image. After initial positioning, the robot spends a sustained interval nearly stationary, then moves closer to the oven late in the episode (frames 211–270, image and wrist_image). No opening is visible; the final approach is unfinished rather than a confirmed failed grasp or pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 42 | No |
| 42 | 166 | Yes |
| 166 | 271 | No |

## Failure annotations

### Failure 1

- Frames: 42-166
- Categories: task_not_attempted
- Explanation: Following initial positioning, the gripper remains essentially stationary beside the oven for roughly ten seconds, with no discernible acquisition or opening progress (frames 42, 80, 120, and 165 in image, left_ego_image, and wrist_image). The oven stays closed. This sustained inactivity is visibly unproductive; its underlying cause is not established.
- Recovery: Resume a task-directed approach, align the fingers with the oven handle, establish a secure grasp, and pull along the door’s opening direction while checking clearance. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The delay prevents task progress, but no damage, displaced objects, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place; another approach can begin without environmental resetting or human intervention.