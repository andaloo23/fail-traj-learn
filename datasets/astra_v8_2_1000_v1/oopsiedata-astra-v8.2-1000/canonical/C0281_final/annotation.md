# Episode: C0281

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. The robot approaches the door edge during frames 7–57, but then remains near it without visibly closing it. At frames 180, 300 and 361, image and left_ego_image still show the door open and the oven interior exposed; wrist_image shows the gripper beside the door edge. This is visible noncompletion with sustained unproductive behavior, not merely an outcome hidden by the recording ending.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 58 | No |
| 58 | 362 | Yes |

## Failure annotations

### Failure 1

- Frames: 58-362
- Categories: task_not_attempted
- Explanation: Following the approach, the robot stays in nearly the same position beside the open door, with only small adjustments and no visible closing progress. Compare frames 58, 120, 240, 300 and 361 in image and left_ego_image; wrist_image likewise shows the fingers remaining beside the door edge. This prolonged unproductive interval prevents task completion. The images do not establish a secure grasp or a mechanical cause.
- Recovery: Reassess the door edge and hinge motion, reposition to establish suitable contact, and move the door along its closing arc while monitoring clearance; verify closure afterward. No human intervention is visibly required.
- Severity: low
- Severity evidence: The oven remains open, but no damage, displaced unrelated objects or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The door and surrounding scene remain available for another attempt; no environmental restoration or human reset is visibly needed.