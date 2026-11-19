# Episode: C0594

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in left_ego_image at frames 0, 26, 200 and 399. After initial robot repositioning, image and wrist_image show the gripper remaining stationary through the rest of the episode, without a visible handle acquisition or door-opening action. The observed failure is sustained inactivity with the task uncompleted, not a confirmed failed grasp or pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 26 | No |
| 26 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 26-400
- Categories: task_not_attempted
- Explanation: Following initial repositioning, the robot remains essentially motionless from frame 26 through frame 399 in image and wrist_image; left_ego_image shows no change to the closed oven door. This approximately 31-second interval provides no discernible progress toward opening the oven. The cause of the inactivity is not visible.
- Recovery: Resume a task-directed approach, align the gripper with the oven handle, acquire it securely and pull along the door’s opening path while checking clearance; no environmental human intervention is visibly needed.
- Severity: low
- Severity evidence: The task remains incomplete, but no robot-caused damage, displacement or meaningful damage risk is visible during the stationary interval.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so another attempt requires no visible environmental reset.