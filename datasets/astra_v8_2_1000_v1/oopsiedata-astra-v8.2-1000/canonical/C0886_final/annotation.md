# Episode: C0886

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed at frame 0 in left_ego_image and remains closed at frames 150, 300 and 399. The robot moves toward the oven during the initial portion, but then stays near its upper front without visibly opening it. image and wrist_image corroborate the prolonged lack of progress. This is visible noncompletion with sustained stalling, rather than an opening action whose completion is merely off-camera; no secure handle acquisition is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 90 | No |
| 90 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 90-400
- Categories: task_not_attempted
- Explanation: After the initial approach, the gripper remains near the oven's upper front with only small positional adjustments and no discernible opening progress. Frames 90, 140, 180, 300 and 399 in left_ego_image show the door remaining closed; image and wrist_image show the largely unchanged robot pose. The extended idle interval, including the small adjustments, does not establish a grasp or productive pull.
- Recovery: Reobserve the handle, align the fingers around it, establish a secure grasp, and pull along the door's opening trajectory while monitoring clearance. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced scene objects or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; another attempt requires robot repositioning rather than environmental resetting or human intervention.