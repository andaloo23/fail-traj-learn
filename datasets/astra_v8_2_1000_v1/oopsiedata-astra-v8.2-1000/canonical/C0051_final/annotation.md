# Episode: C0051

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in image and left_ego_image from frame 0 through frame 399. The robot approaches the oven’s upper front area during frames 10–46, but subsequently makes only small repeated movements without opening the door (frames 47–399, also visible in wrist_image). This is sustained visible lack of progress, not merely completion left unconfirmed by the recording ending; secure handle acquisition is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 47 | No |
| 47 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 47-400
- Categories: task_not_attempted
- Explanation: After approaching the oven, the gripper stays around the same upper-front position with small repeated shifts for the remainder of the episode rather than progressing to door opening. Compare frames 47, 100, 200, 300 and 399 in image and left_ego_image; wrist_image shows the repeated small motions while the oven remains closed. This prolonged unproductive interval establishes stalling, but the views do not establish a secure grasp or a mechanical cause.
- Recovery: Reassess the handle position, reposition the gripper to acquire it securely, and then pull along the door’s opening path while monitoring door movement; stop and reassess if it does not move. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced surrounding objects or meaningful damage risk is visible in image and left_ego_image through frame 399.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state, so another handle-acquisition attempt needs no environmental reset or human intervention.