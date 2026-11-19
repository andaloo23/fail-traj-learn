# Episode: C0076

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed at frame 0 in left_ego_image. The robot moves toward the oven during frames 0–76, but then remains in essentially the same pose through frame 399 in image and wrist_image. The door remains visibly closed in left_ego_image at frames 77, 200 and 399; no opening is observed. The visible failure is sustained lack of progress, not an established failed grasp or abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 77 | No |
| 77 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 77-400
- Categories: task_not_attempted
- Explanation: After the initial approach, the robot stays essentially stationary beside the oven for approximately 27 seconds, with no visible handle acquisition or door movement. Frames 77, 120, 200, 300 and 399 in image and wrist_image show the unchanged gripper pose, while left_ego_image shows the oven still closed. This sustained stalling does not advance the task; its underlying cause is not visible.
- Recovery: Resume task-directed alignment with the oven handle, establish a secure grasp, and pull along the door’s opening path while monitoring clearance and door movement. No environmental human intervention is visibly needed.
- Severity: low
- Severity evidence: The task remains incomplete, but no object displacement, damage or meaningful damage risk is visible during the stationary interval.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; another attempt requires no visible environmental reset.