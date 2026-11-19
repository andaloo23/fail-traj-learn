# Episode: C0125

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven starts open (frame 0, image and left_ego_image). The robot raises the door partway at frames 57–70, but it swings back down at frames 71–75 rather than closing. The door remains visibly open through frame 141 in image, left_ego_image and wrist_image; this is a visibly unsuccessful closing attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 71 | No |
| 71 | 79 | Yes |
| 79 | 142 | Yes |

## Failure annotations

### Failure 1

- Frames: 71-79
- Categories: manipulation
- Explanation: After raising the door partway at frames 57–70, the robot fails to maintain its closing motion: the door swings downward at frames 71–75 and returns to its open position while the gripper moves away (image and left_ego_image). The reversal is also visible in wrist_image. The precise contact or release mechanism is unclear.
- Recovery: Reposition at the door handle, establish controlled contact, and guide the door through its full closing arc before releasing; no human intervention is visibly required.
- Severity: low
- Severity evidence: The door returns to its open position without visible damage or disturbance to surrounding objects.
- Resetability: immediate
- Resetability evidence: The oven remains accessible and open, allowing another attempt without environmental resetting.

### Failure 2

- Frames: 79-142
- Categories: task_not_attempted
- Explanation: From frame 79 through frame 141, the gripper remains nearly stationary beside the open oven without a renewed closing motion (image, left_ego_image and wrist_image). This sustained inactivity does not advance the unfinished task; the images do not establish its underlying cause.
- Recovery: Resume a controlled approach to the handle and close the door while verifying its final position; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage or additional harmful scene change is visible during the stall.
- Resetability: immediate
- Resetability evidence: No objects need restoring or retrieving; the unchanged open oven is ready for a renewed attempt.