# Episode: C0425

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains upright and closed in left_ego_image at frames 0, 55, 200 and 399. The robot initially repositions near the oven, but image and wrist_image show no subsequent opening action during the prolonged stationary remainder. Completion is not observed; the visible local failure is sustained inactivity, rather than a confirmed failed handle grasp or pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 55 | No |
| 55 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 55-400
- Categories: task_not_attempted
- Explanation: After its initial repositioning, the robot remains essentially stationary near the oven from frame 55 through frame 399, with no discernible acquisition or pulling of the handle. The unchanged gripper pose in image and wrist_image and the closed door in left_ego_image at frames 55, 200 and 399 establish approximately 29 seconds of unproductive stalling. The images do not establish its underlying cause.
- Recovery: Resume task-directed alignment with the oven handle, acquire it securely, and pull along the door’s opening trajectory while checking door motion and clearance; no human intervention is visibly required.
- Severity: low
- Severity evidence: The oven remains closed, with no visible damage, displaced scene objects or meaningful damage risk caused by the stationary interval.
- Resetability: immediate
- Resetability evidence: The scene remains usable and unchanged during the stall, so another opening attempt requires no environmental reset or visible human intervention.