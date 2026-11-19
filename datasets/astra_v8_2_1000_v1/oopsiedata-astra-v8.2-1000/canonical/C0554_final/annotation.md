# Episode: C0554

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 399 in left_ego_image and image. The robot initially approaches the oven, but then remains near its upper front with only small adjustments and no visible opening; wrist_image at frames 70, 188, 240 and 399 shows the fingers remaining clear of a confirmed handle grasp. This is an observed failure to complete the task with sustained stalling, not a confirmed failed grasp or abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 70 | No |
| 70 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 70-400
- Categories: task_not_attempted
- Explanation: Following the initial approach, the robot stays nearly stationary near the oven from frame 70 onward, with small position changes around frames 189-230 but no discernible acquisition or door-opening progress. In left_ego_image and image at frames 70, 188, 240 and 399, the door stays closed; wrist_image shows no established handle possession. This prolonged unproductive interval prevents completion; its underlying cause is not visible.
- Recovery: Reobserve the oven handle, align the fingers for a secure grasp, and then pull along the door's opening path while monitoring clearance and door motion; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state, so another task-directed attempt requires no environmental reset or human intervention.