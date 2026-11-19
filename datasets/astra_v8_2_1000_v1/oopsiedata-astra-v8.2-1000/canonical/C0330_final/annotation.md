# Episode: C0330

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. The robot approaches the door/handle region during frames 10–128, but the door remains lowered and the oven opening remains exposed at frames 200, 320 and 399 in image and left_ego_image. Completion is visibly not achieved; the episode includes sustained unproductive hovering rather than merely ending during an otherwise progressing closure. No damage or unrelated object displacement is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 130 | No |
| 130 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 130-400
- Categories: task_not_attempted
- Explanation: Following the approach and small alignment movements, the robot remains near the open door with only minor pose changes and no meaningful closing progress throughout frames 130–399. image and left_ego_image show the door remaining lowered at frames 130, 200, 300 and 399; wrist_image shows the gripper staying beside the door edge. This prolonged unproductive interval constitutes stalling. The views do not clearly establish a secure handle grasp or a mechanical cause.
- Recovery: Reassess the handle position, align the gripper for secure contact, and lift the door along its hinge arc while checking that it moves toward closure; verify closure before withdrawing. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced unrelated objects or concrete damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven remains open and accessible with the surrounding scene intact; another attempt can begin without environmental resetting or human intervention.