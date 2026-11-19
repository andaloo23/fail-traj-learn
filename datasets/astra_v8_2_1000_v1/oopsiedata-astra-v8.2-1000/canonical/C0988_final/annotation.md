# Episode: C0988

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. The robot approaches the door/handle region during frames 8–67, but then remains there with only small adjustments and no meaningful closing progress. At frame 393, image and left_ego_image still show the door lowered and the oven cavity exposed; wrist_image also shows the open door beside the gripper. The observed task is not completed, and sustained stalling is visible rather than merely an unconfirmed final outcome.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 68 | No |
| 68 | 394 | Yes |

## Failure annotations

### Failure 1

- Frames: 68-394
- Categories: task_not_attempted
- Explanation: After approaching the door, the robot remains essentially stationary near its handle for a sustained interval, with occasional small adjustments that do not close it. Frames 68, 120, 200, 300 and 393 in image and left_ego_image show the door remaining open; wrist_image shows little change in the gripper–door arrangement. This prolonged lack of progress establishes stalling, but the images do not establish a mechanical fault or a secure grasp that would justify a more specific manipulation diagnosis.
- Recovery: Reassess the handle position, establish a verified grasp or suitable supporting contact, and lift the door along its hinge arc until closed, then verify closure. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains unfinished, but no damage, displaced unrelated objects, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven remains open and accessible, and the surrounding scene is unchanged; another properly aligned attempt requires no visible environmental reset or human intervention.