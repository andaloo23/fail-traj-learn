# Episode: C0835

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The robot approaches the oven during frames 0–52, but the door remains closed in image and left_ego_image. Frames 53–173 show sustained hovering with only small adjustments; wrist_image does not establish acquisition of the handle or an opening motion. The final closed door visibly establishes noncompletion, rather than merely leaving completion outside the camera view.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 53 | No |
| 53 | 174 | Yes |

## Failure annotations

### Failure 1

- Frames: 53-174
- Categories: task_not_attempted
- Explanation: After approaching, the robot remains near the oven with little change in position throughout frames 53–173 in image, left_ego_image and wrist_image. No discernible handle acquisition or door-opening movement follows, and the door stays closed. This prolonged unproductive interval constitutes stalling; the images do not establish a mechanical fault or failed grasp.
- Recovery: Resume task-directed alignment with the oven handle, acquire it securely, and open the door along its hinge path while monitoring clearance. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible during the stall.
- Resetability: immediate
- Resetability evidence: The oven remains closed and the surrounding scene is unchanged, so another attempt requires no environmental reset or human intervention.