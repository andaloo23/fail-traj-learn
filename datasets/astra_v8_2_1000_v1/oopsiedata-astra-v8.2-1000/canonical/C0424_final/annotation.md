# Episode: C0424

## Episode annotation

- Language task: Open the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven starts closed (frame 0, image and left_ego_image). After approaching its handle, the robot remains nearly stationary for a sustained interval (frames 78–150, left_ego_image and wrist_image). It subsequently pulls the door outward (frames 180–193, image and left_ego_image), leaving it visibly open as the gripper withdraws through frame 228. No unintended object displacement or damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 78 | No |
| 78 | 151 | Yes |
| 151 | 229 | No |

## Failure annotations

### Failure 1

- Frames: 78-151
- Categories: task_not_attempted
- Explanation: Following the approach, the gripper remains in essentially the same position near the oven for approximately six seconds without discernible progress toward opening it (frames 78, 100, 125 and 150, left_ego_image and wrist_image); the door stays closed in image. This is sustained stalling rather than a visibly failed grasp; the images do not establish its underlying cause. Renewed movement begins at frame 151.
- Recovery: Resume task-directed handle alignment, establish a secure grasp, and pull along the door’s opening path; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The interval delays completion but produces no visible damage, object displacement, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their existing usable states, so the robot can continue without an environmental reset or human intervention.