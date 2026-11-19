# Episode: C0346

## Episode annotation

- Language task: Open the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven begins closed (frame 0, image and left_ego_image). Several small opening movements are followed by the door returning closed as the gripper retreats (frames 101–118, 162–188, and 240–258, image). The final attempt opens the door substantially at frames 324–333; it remains open through frame 349, exposing the interior in image and left_ego_image. No damage or displacement of unrelated objects is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 109 | No |
| 109 | 118 | Yes |
| 118 | 173 | No |
| 173 | 188 | Yes |
| 188 | 247 | No |
| 247 | 258 | Yes |
| 258 | 350 | No |

## Failure annotations

### Failure 1

- Frames: 109-118
- Categories: grasp
- Explanation: Following a slight outward movement of the door at frames 101–108, the gripper withdraws without retaining the handle and the door returns closed at frames 109–117 (image and left_ego_image). This attempt does not leave the oven open; the exact contact failure is obscured.
- Recovery: Reapproach and align the fingers around the handle, establish secure retention, and pull along the door’s opening arc; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The door returns closed without visible damage or disturbance of nearby objects.
- Resetability: immediate
- Resetability evidence: The oven and accessible handle remain in place, allowing another attempt without environmental resetting.

### Failure 2

- Frames: 173-188
- Categories: grasp
- Explanation: The door moves slightly outward at frames 162–172, but closes again while the gripper moves away empty at frames 173–187 (image, corroborated by left_ego_image). The robot again fails to retain the handle through the opening movement.
- Recovery: Adjust the handle grasp before pulling, verify retention through the initial movement, and continue opening under controlled motion; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only the opening attempt is defeated; no damage, falling objects, or other harmful consequences are visible.
- Resetability: immediate
- Resetability evidence: The closed oven remains usable and accessible, with no scene restoration needed.

### Failure 3

- Frames: 247-258
- Categories: grasp
- Explanation: Another slight opening at frames 240–246 is lost as the gripper retreats at frames 247–257, leaving the door closed rather than carrying it through its opening arc (image and left_ego_image). The images establish unsuccessful handle retention, not its hidden cause.
- Recovery: Reposition for a more secure handle grasp and maintain it while following the hinge arc until the door is stably open; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The unsuccessful attempt causes no visible damage or meaningful disturbance beyond the door returning closed.
- Resetability: immediate
- Resetability evidence: The handle remains available for an immediate retry without moving or repairing anything in the environment.