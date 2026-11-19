# Episode: C0435

## Episode annotation

- Language task: Close the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. After a prolonged interval with essentially no progress, the robot raises the door during frames 298–317; it is upright and closed at frames 318–352 in left_ego_image, corroborated by image. No unintended object displacement or damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 33 | No |
| 33 | 209 | Yes |
| 209 | 353 | No |

## Failure annotations

### Failure 1

- Frames: 33-209
- Categories: task_not_attempted
- Explanation: Following initial positioning, the robot remains essentially stationary beside the open oven for about 15 seconds without advancing closure; frames 33, 80, 140 and 208 in left_ego_image and wrist_image show nearly unchanged gripper positioning, while image confirms the door remains open. Small adjustments do not produce discernible progress. Task-directed movement resumes at frame 209.
- Recovery: Resume alignment with the door handle or accessible door edge, establish controlled contact, and raise the door along its hinge path until closed; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is delay with the oven left open; no damage or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so the robot can continue the closing attempt without environmental resetting or human intervention.