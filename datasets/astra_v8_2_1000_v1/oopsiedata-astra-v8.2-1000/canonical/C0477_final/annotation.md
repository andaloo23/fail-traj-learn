# Episode: C0477

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 247 in left_ego_image. The robot initially raises and positions its gripper near the oven’s upper front (frames 0–63, left_ego_image and wrist_image), then remains nearly stationary without opening the door. This is visible noncompletion with sustained stalling, not a confirmed failed handle grasp; possession of the handle is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 64 | No |
| 64 | 248 | Yes |

## Failure annotations

### Failure 1

- Frames: 64-248
- Categories: task_not_attempted
- Explanation: Following the initial positioning, the gripper stays in essentially the same pose near the oven for the remainder of the episode, with only small adjustments and no discernible opening progress (frames 64, 100, 164, 200 and 247, left_ego_image and wrist_image). The door remains closed throughout this sustained unproductive interval; the images do not establish a grasp or a mechanical cause.
- Recovery: Reassess the handle location, align the fingers to acquire it, verify engagement, and pull along the door’s opening path while monitoring clearance. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible in image or left_ego_image through frame 247.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place with the door closed, so another attempt requires no visible environmental reset or human intervention.