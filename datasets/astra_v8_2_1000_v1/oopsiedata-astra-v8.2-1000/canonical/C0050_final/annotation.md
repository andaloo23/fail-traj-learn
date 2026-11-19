# Episode: C0050

## Episode annotation

- Language task: Open the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven starts closed (frame 0, left_ego_image). After approaching its handle, the robot remains nearly motionless for a sustained interval before resuming movement. The door then rotates outward and downward in frames 140–168 (image and left_ego_image), and remains open after the gripper withdraws through frame 211. No displacement or damage to unrelated objects is visibly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 75 | No |
| 75 | 130 | Yes |
| 130 | 212 | No |

## Failure annotations

### Failure 1

- Frames: 75-130
- Categories: task_not_attempted
- Explanation: The robot sustains a nearly stationary pose beside the closed oven without visible opening progress across frames 75–129 (image, left_ego_image, and wrist_image). This prolonged stall interrupts an otherwise task-directed approach; its underlying cause is not visible. Opening movement resumes from approximately frame 130.
- Recovery: Resume task-directed handle engagement and controlled pulling along the door’s hinge motion, verifying that the door moves; no human intervention is visibly required.
- Severity: low
- Severity evidence: The stall delays completion but causes no visible damage, object displacement, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so execution can continue without an environmental reset or human intervention.