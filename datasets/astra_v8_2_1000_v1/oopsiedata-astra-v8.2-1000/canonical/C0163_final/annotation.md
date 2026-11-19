# Episode: C0163

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The robot approaches the oven handle and moves the door slightly outward at frames 121–150, but the door returns to its closed position at frames 161–170 in image and left_ego_image. It remains closed through frame 399 while the robot stays near the handle. This is a visibly unsuccessful opening attempt, not merely an unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 161 | No |
| 161 | 181 | Yes |
| 181 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 161-181
- Categories: manipulation
- Explanation: After moving the oven door slightly outward at frames 121–150, the robot fails to maintain that opening: the door swings back toward its original closed position at frames 161–170 in image and left_ego_image. The gripper remains near the handle, but wrist_image does not establish whether it slipped or deliberately released; the visible failure is loss of opening progress.
- Recovery: Reassess the handle engagement, establish a secure grasp, and guide the door through its opening arc until it rests stably open before releasing; no human intervention is visibly required.
- Severity: low
- Severity evidence: The door returns closed without visible damage, displacement of unrelated objects, or a supported meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The oven remains intact and accessible in its closed position, so another attempt requires no environmental reset.

### Failure 2

- Frames: 181-400
- Categories: task_not_attempted
- Explanation: The robot remains essentially stationary near the handle with the oven closed throughout frames 181–399, as shown in image, left_ego_image, and wrist_image. This sustained interval of roughly 18 seconds shows no renewed acquisition or opening progress.
- Recovery: Resume a task-directed attempt by checking the door and handle position, adjusting the gripper, and opening the door with verified engagement; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The observed consequence is an unfinished task and prolonged inactivity, with no visible damage or harmful scene change.
- Resetability: immediate
- Resetability evidence: Stalling leaves the scene unchanged and the handle accessible; no physical reset is needed to retry.