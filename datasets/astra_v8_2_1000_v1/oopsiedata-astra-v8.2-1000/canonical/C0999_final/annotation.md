# Episode: C0999

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The door starts open in frame 0 (image, left_ego_image), rises toward closure in frames 55–80, but lowers again in frames 83–132. Subsequent adjustments do not close it: frames 294 and 399 (image, left_ego_image, wrist_image) show the door still projecting outward with the interior exposed. This is a visibly unsuccessful closing attempt, not merely an unconfirmed final latch.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 83 | No |
| 83 | 193 | Yes |
| 193 | 294 | No |
| 294 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 83-193
- Categories: manipulation
- Explanation: After raising the door toward the oven in frames 55–80, the robot reverses that progress: the door lowers through frames 83–132 (image, left_ego_image). Further small up-and-down adjustments in frames 147–192 leave it open rather than completing closure. Door motion follows the robot's handling, but the images do not establish why closure fails.
- Recovery: Reassess the handle contact and hinge trajectory, establish stable control, and guide the door upward and inward through its closing arc; check for resistance rather than forcing it. No human intervention is visibly required.
- Severity: low
- Severity evidence: The door remains open; no breakage, displaced contents, or other meaningful damage is visible in image and left_ego_image through frame 192.
- Resetability: immediate
- Resetability evidence: The oven and door remain accessible and intact, allowing another closing attempt without environmental resetting.

### Failure 2

- Frames: 294-400
- Categories: task_not_attempted
- Explanation: Following repositioning along the open door, the robot remains essentially stationary from frame 294 through frame 399 (image, left_ego_image, wrist_image). The door stays open throughout this roughly nine-second interval, establishing sustained unproductive stalling rather than a brief alignment pause.
- Recovery: Resume a controlled closing attempt after verifying the gripper's contact with the door and a clear closing path; confirm that the door is seated before stopping. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The observed consequence is failure to close the oven; the final views show no damage or harmful scene disturbance.
- Resetability: immediate
- Resetability evidence: The unchanged open-door configuration permits a renewed attempt without cleanup, repair, or manual object replacement.