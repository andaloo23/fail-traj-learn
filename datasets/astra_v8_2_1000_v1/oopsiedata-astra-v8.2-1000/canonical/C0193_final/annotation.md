# Episode: C0193

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 360 in image and left_ego_image. The robot initially moves toward the oven’s upper front area (frames 0–43), then stays near that area with only small movements for the remainder of the episode; wrist_image also shows this prolonged lack of progress. Opening is not achieved visibly; sustained stalling is observable, but a failed handle grasp or pull is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 44 | No |
| 44 | 361 | Yes |

## Failure annotations

### Failure 1

- Frames: 44-361
- Categories: task_not_attempted
- Explanation: Following the initial approach, the gripper remains near the oven’s upper front area with minor oscillations but no visible door-opening progress from frames 44–360, as shown in image, left_ego_image and wrist_image. This prolonged unproductive interval constitutes sustained stalling; the images do not establish handle possession or a mechanical cause.
- Recovery: Reassess the handle position, align the gripper for a secure acquisition, and execute a controlled opening motion while checking that the door moves; no human intervention is visibly required.
- Severity: low
- Severity evidence: The oven remains closed and the task is prevented from succeeding; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so another attempt can begin without an environmental reset or human intervention.