# Episode: C0014

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed at frame 0 and remains closed at frames 100, 250 and 399 in left_ego_image and image. The robot initially moves toward the oven, then remains near its upper front area with only small positional changes; wrist_image shows no established handle acquisition or opening motion. Completion is not observed, and sustained unproductive hovering is visible rather than merely an unfinished opening action.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 33 | No |
| 33 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 33-400
- Categories: task_not_attempted
- Explanation: After the initial approach, the gripper hovers near the oven with small adjustments but no discernible progress toward opening it. Frames 33, 100, 200, 300 and 399 in left_ego_image show essentially the same gripper–oven arrangement and a closed door; wrist_image shows no confirmed handle grasp. This prolonged interval is sustained stalling, not a brief alignment pause; its underlying cause is not visible.
- Recovery: Reassess the handle position, align the gripper for a secure acquisition, and then open the door along its hinge motion while checking clearance and door movement. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains uncompleted, but image and left_ego_image show no displaced unrelated objects, damage or concrete damage risk during the stalled interval.
- Resetability: immediate
- Resetability evidence: The oven remains closed and the surrounding scene remains unchanged, so another task-directed attempt can begin without an environmental reset or human intervention.