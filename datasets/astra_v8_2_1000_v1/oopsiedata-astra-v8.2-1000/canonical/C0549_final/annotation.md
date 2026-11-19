# Episode: C0549

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 399 in left_ego_image. The robot approaches the upper door/handle area, with closer alignment visible in image and wrist_image at frames 200–280, but no door-opening motion follows. Completion is not observed; sustained stationary intervals are visible, while a failed handle acquisition or failed pull cannot be established from the images.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 51 | No |
| 51 | 141 | Yes |
| 141 | 281 | No |
| 281 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 51-141
- Categories: task_not_attempted
- Explanation: Following the initial approach, the gripper remains nearly stationary above the oven door for roughly 7.5 seconds, without acquiring the handle or opening the door; compare frames 51, 90, and 140 in image, left_ego_image, and wrist_image. This sustained pause does not visibly advance the task; gradual approach resumes around frame 141.
- Recovery: Resume visual alignment with the door handle and approach with the fingers positioned to capture it; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task is delayed, but no damage, displaced objects, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so another approach requires no environmental reset.

### Failure 2

- Frames: 281-400
- Categories: task_not_attempted
- Explanation: After approaching the handle region, the robot remains in essentially the same pose through the end, with only small adjustments and no visible door movement; compare frames 281, 330, and 399 in image, left_ego_image, and wrist_image. This approximately ten-second interval is persistently unproductive. The views do not establish a secure grasp or an unsuccessful pulling action.
- Recovery: Reassess finger placement around the handle, establish a verified grasp, and then pull along the door's hinge-constrained opening path while monitoring door movement; no human intervention is visibly required.
- Severity: low
- Severity evidence: The oven remains closed, with no visible damage or harmful side effect from the stationary positioning.
- Resetability: immediate
- Resetability evidence: No scene restoration is needed; the robot can reposition and attempt handle acquisition again.
