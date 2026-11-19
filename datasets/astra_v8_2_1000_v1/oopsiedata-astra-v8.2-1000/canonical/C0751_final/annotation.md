# Episode: C0751

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The drawers are closed at frame 0 in left_ego_image. The robot approaches the cabinet during frames 1–103, but neither drawer visibly opens. From frame 104 through frame 399, image and left_ego_image show the arm remaining beside the cabinet with no meaningful task progress; wrist_image does not establish a handle grasp or successful pull. Completion is unconfirmed, and sustained stalling is visible rather than a clearly demonstrated failed grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 104 | No |
| 104 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 104-400
- Categories: task_not_attempted
- Explanation: After approaching the cabinet, the robot remains essentially stationary beside it from frame 104 through frame 399. In image and left_ego_image, the drawers remain closed at frames 104, 200, 300 and 399; wrist_image shows no discernible acquisition-and-pull sequence. This prolonged lack of progress constitutes sustained stalling; its underlying cause is not visible.
- Recovery: Re-localize the drawer handle, align the gripper with it, establish a secure grasp, and pull along the drawer’s opening direction while checking for movement. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced unrelated objects, or meaningful damage risk is visible during the stalled interval.
- Resetability: immediate
- Resetability evidence: The cabinet and surrounding objects remain in their original usable state, so another task-directed attempt requires no environmental reset or visible need for human intervention.