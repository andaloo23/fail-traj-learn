# Episode: C0898

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven is closed at frame 0 in image and left_ego_image and remains closed at frame 399. The gripper approaches the oven during frames 0–77, but then remains near it without visible door opening for most of the episode (frames 78–399, image, left_ego_image, and wrist_image). Completion is not observed; sustained inactivity is visible, but a completed failed handle grasp or pull is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 78 | No |
| 78 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 78-400
- Categories: task_not_attempted
- Explanation: Following the initial approach, the gripper stays almost stationary near the oven, with only small later adjustments and no discernible opening action. Frames 78, 150, 210, 280, and 399 in image and wrist_image show the persistent near-oven pose; left_ego_image shows the door remaining closed. This prolonged stall does not advance the task. The images do not establish handle possession or a hidden cause.
- Recovery: Resume task-directed alignment with the oven handle, verify a secure grasp, and move the door along its opening path while monitoring clearance and resistance. No human intervention is visibly required; seek assistance if safe motion cannot resume.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and nearby plate and spoon remain in their original usable state; another attempt requires no visible environmental reset or human intervention.