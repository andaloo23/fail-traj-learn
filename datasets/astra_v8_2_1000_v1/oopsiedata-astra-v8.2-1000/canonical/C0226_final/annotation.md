# Episode: C0226

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in image and left_ego_image from frame 0 through frame 399. The robot initially repositions near the oven, but wrist_image shows no confirmed handle acquisition or opening; by frames 88–399 the gripper remains essentially stationary. Completion is not observed, and sustained inactivity is visible rather than a confirmed failed pull or grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 88 | No |
| 88 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 88-400
- Categories: task_not_attempted
- Explanation: After initial positioning, the robot remains essentially stationary without opening the oven for approximately 26 seconds; frames 88, 180, 300 and 399 in image and left_ego_image show the unchanged closed door, while wrist_image shows the unchanged gripper pose. This sustained stall does not advance the task. No hidden cause or abnormal termination is established.
- Recovery: Resume task-directed positioning, align the gripper with the oven handle, establish a secure grasp, and pull along the door's opening path while monitoring clearance; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain unchanged, so another attempt can begin without an environmental reset or human intervention.