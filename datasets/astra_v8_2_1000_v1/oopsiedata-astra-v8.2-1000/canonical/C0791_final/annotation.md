# Episode: C0791

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in left_ego_image at frames 0, 100, 200, 300 and 399. Initial positioning brings the gripper near the oven, but image and wrist_image show no subsequent effective handle acquisition or opening motion. The episode ends after sustained inactivity rather than during a visibly progressing opening attempt; no abnormal termination or damage is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 33 | No |
| 33 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 33-400
- Categories: task_not_attempted
- Explanation: After initial positioning, the robot remains essentially stationary near the closed oven from frame 33 through frame 399, with only small positional changes. In wrist_image the fingers remain beside the oven without a visible opening action, while left_ego_image confirms the unchanged closed door at frames 33, 100, 200, 300 and 399. This sustained stall does not advance the task; the images do not establish a failed grasp or a mechanical cause.
- Recovery: Reassess the handle position, align the gripper for a secure acquisition, and execute a controlled opening motion while checking door movement and clearance. No environmental human intervention is visibly needed.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible in image and left_ego_image through frame 399.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; another attempt requires no visible environmental reset or human intervention.