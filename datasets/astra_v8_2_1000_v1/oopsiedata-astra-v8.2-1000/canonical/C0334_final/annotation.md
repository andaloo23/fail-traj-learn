# Episode: C0334

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in left_ego_image at frames 0, 48, 90 and 133. The robot moves toward the oven during frames 10–48, then remains nearly stationary nearby through frame 133 without visible opening progress. image and wrist_image corroborate the lack of door movement; a secure handle grasp is not established. Completion is unconfirmed, with sustained stalling visible rather than a demonstrated failed pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 49 | No |
| 49 | 134 | Yes |

## Failure annotations

### Failure 1

- Frames: 49-134
- Categories: task_not_attempted
- Explanation: After approaching the oven, the robot remains in essentially the same nearby pose from frame 49 through frame 133, with only small positional changes and no discernible opening progress. left_ego_image shows the door staying closed at frames 49, 90 and 133; wrist_image shows the gripper hovering beside the oven without an established handle acquisition. This prolonged interval is unproductive rather than a brief alignment pause.
- Recovery: Re-localize the door handle, align the gripper, establish a secure grasp and open the door along its hinge motion while checking clearance. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but image and left_ego_image show no damage, displaced objects or other harmful consequences.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; another approach can be attempted without environmental resetting or human intervention.