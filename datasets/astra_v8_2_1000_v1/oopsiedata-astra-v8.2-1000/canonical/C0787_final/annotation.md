# Episode: C0787

## Episode annotation

- Language task: Close the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. After approaching the door, the robot remains nearly stationary without closing it during frames 113–178. It then raises the door during frames 190–208; the upright, closed door is visible in left_ego_image and wrist_image at frame 208 and remains closed after the robot withdraws, including frame 399. No damage or displacement of unrelated objects is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 113 | No |
| 113 | 179 | Yes |
| 179 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 113-179
- Categories: task_not_attempted
- Explanation: In image, left_ego_image and wrist_image, the gripper stays near the open oven door with only small adjustments during frames 113–178. The door remains open with no discernible closing progress for approximately 5.5 seconds, constituting sustained stalling rather than the preceding approach. Task-directed movement resumes at frame 179.
- Recovery: Resume alignment with the door handle or suitable contact surface and lift the door along its hinge motion, then verify closure; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The stall delays completion but causes no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in a usable state; the robot can continue the closing attempt without environmental resetting or human intervention.