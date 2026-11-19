# Episode: C0499

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in left_ego_image at frames 0, 134, 250 and 399. The robot moves toward the oven’s upper-front area during frames 0–133, but no door-opening motion is visible; image and wrist_image also show the subsequent prolonged stationary pose. Completion is not merely hidden or unconfirmed: the final visible door is still closed. Secure handle acquisition is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 134 | No |
| 134 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 134-400
- Categories: task_not_attempted
- Explanation: Following its approach, the robot remains essentially stationary near the oven for approximately 22 seconds without opening the door or visibly adjusting its approach. Frames 134, 200, 300 and 399 in image, left_ego_image and wrist_image show the sustained unchanged pose and closed oven. This establishes prolonged unproductive stalling, but not a failed grasp, mechanical malfunction or abnormal termination.
- Recovery: Reassess the handle position, align the gripper, acquire the handle and pull along the door’s opening path while monitoring clearance and door motion; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, with no visible damage, displaced objects or meaningful damage risk established by the stationary pose.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; another opening attempt requires no environmental reset or human intervention.