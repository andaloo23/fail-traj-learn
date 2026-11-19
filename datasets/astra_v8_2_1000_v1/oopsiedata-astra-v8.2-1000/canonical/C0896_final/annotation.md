# Episode: C0896

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 399 in left_ego_image, corroborated by image. The robot approaches the oven during frames 0–71, but then remains near its upper front with only small adjustments and no visible opening progress through frame 399 (left_ego_image and wrist_image). Completion is not observed; sustained unproductive hovering is visible, rather than a confirmed failed handle grasp or pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 72 | No |
| 72 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 72-400
- Categories: task_not_attempted
- Explanation: After approaching the oven, the robot stays near its upper front without discernible progress toward opening it. Frames 72, 120, 200, 300 and 399 in left_ego_image show the door unchanged and closed; wrist_image shows essentially the same hovering gripper pose, apart from minor adjustments. This extended interval establishes sustained stalling, but does not establish handle possession or a mechanical cause.
- Recovery: Reassess the handle location, align the fingers to acquire it, verify engagement, and execute a controlled opening motion along the door's hinge path. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible in image or left_ego_image through frame 399.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; another task-directed attempt requires no visible environmental reset or human intervention.