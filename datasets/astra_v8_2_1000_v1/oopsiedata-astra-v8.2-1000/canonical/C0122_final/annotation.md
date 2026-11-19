# Episode: C0122

## Episode annotation

- Language task: Close the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven starts open (frame 0, image and left_ego_image). Several approaches and empty upward withdrawals leave the door open, and a prolonged pause occurs before another attempt. The final lift rotates the door upright against the oven at frames 321–333; it remains closed through frame 354 (image, left_ego_image, and wrist_image). No damage or displacement of unrelated objects is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 84 | No |
| 84 | 112 | Yes |
| 112 | 136 | No |
| 136 | 156 | Yes |
| 156 | 178 | No |
| 178 | 211 | Yes |
| 211 | 248 | No |
| 248 | 263 | Yes |
| 263 | 355 | No |

## Failure annotations

### Failure 1

- Frames: 84-112
- Categories: grasp
- Explanation: After positioning at the door handle, the gripper lifts away without bringing the door with it (frames 84–94, image and left_ego_image); the door remains down through frame 111. The wrist_image view also shows the door separated from the rising fingers, supporting failed acquisition rather than a successful closing motion.
- Recovery: Reapproach the handle, align the fingers around it, and verify engagement with a small controlled lift before continuing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The door remains open without visible damage or disturbance to surrounding objects.
- Resetability: immediate
- Resetability evidence: The handle remains accessible in its original open-door configuration; no environmental reset is required.

### Failure 2

- Frames: 136-156
- Categories: grasp
- Explanation: Following another approach, the gripper again rises while the door stays open and stationary (frames 136–153, image and left_ego_image). The separation visible in wrist_image supports another unsuccessful handle acquisition.
- Recovery: Lower and realign the gripper with the handle, confirm secure engagement, then follow the door's hinge arc; no human intervention is visibly needed.
- Severity: low
- Severity evidence: This attempt only delays closure; no damage or harmful side effect is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding scene remain usable without repositioning any objects.

### Failure 3

- Frames: 178-211
- Categories: task_not_attempted
- Explanation: The robot holds essentially the same pose beside the still-open door for approximately 2.75 seconds, without visible acquisition, door movement, or useful alignment progress (frames 178, 192, and 210, image, left_ego_image, and wrist_image). This is a sustained unproductive pause rather than the preceding approach.
- Recovery: Resume deliberate handle alignment and a controlled closing attempt; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The pause causes delay only, with no visible damage or environmental disruption.
- Resetability: immediate
- Resetability evidence: No scene changes occur during the pause, so another attempt can begin directly.

### Failure 4

- Frames: 248-263
- Categories: grasp
- Explanation: The door briefly lifts at frames 244–247 but returns downward as the gripper continues upward at frames 248–258 (image and left_ego_image). The wrist_image view shows separation from the door, indicating loss of engagement before closure.
- Recovery: Reengage the handle with a more secure grip and maintain support throughout the upward hinge motion; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The door returns to its open position; no breakage or disturbance of the oven contents is visible.
- Resetability: immediate
- Resetability evidence: The open door remains accessible and intact, allowing a direct retry without environmental intervention.
