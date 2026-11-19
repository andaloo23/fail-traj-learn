# Episode: C0933

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in image and left_ego_image from frame 0 through frame 399. Initial robot repositioning is visible in frames 0–74, especially in wrist_image, but no handle acquisition or door opening is established. The robot then remains essentially stationary through the end, with only slight positional changes. Completion is unconfirmed because no opening occurs visibly; the supported local failure is sustained inactivity, not a demonstrated failed grasp or pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 75 | No |
| 75 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 75-400
- Categories: task_not_attempted
- Explanation: After initial repositioning, the gripper stays above and apart from the oven handle without discernible acquisition or opening progress. Frames 75, 120, 200, 300 and 399 in wrist_image show essentially the same idle configuration, while image and left_ego_image show the door remaining closed. Slight intermediate positional changes do not develop into a task-directed attempt; this is sustained stalling rather than an ordinary brief pause.
- Recovery: Resume by locating the oven handle, aligning the gripper, establishing a secure grasp and pulling along the door's opening path while monitoring clearance. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible in image and left_ego_image through frame 399.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; another approach can begin without an environmental reset or human intervention.