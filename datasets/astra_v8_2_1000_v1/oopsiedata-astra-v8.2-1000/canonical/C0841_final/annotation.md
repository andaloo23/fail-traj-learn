# Episode: C0841

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 399 in left_ego_image and image. The robot approaches the oven during frames 0–73, but then remains near its upper front area with only small positional changes; wrist_image shows no visible handle acquisition or door-opening motion. This is an observed failure to complete the task with sustained stalling, rather than merely an opening action whose completion falls outside the recording.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 74 | No |
| 74 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 74-400
- Categories: task_not_attempted
- Explanation: After approaching the oven, the robot stays at essentially the same near-oven position throughout frames 74–399, with occasional small movements but no discernible progress toward opening it. Frames 74, 150, 250, and 399 in left_ego_image and image show the door unchanged and closed; wrist_image shows the gripper remaining beside the oven without visible acquisition or pulling. The prolonged unproductive interval establishes stalling; its underlying cause is not visible.
- Recovery: Reassess the handle location, align the gripper to acquire it, and verify engagement before pulling along the door’s opening path. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced scene objects, or meaningful damage risk is visible during the stalled interval.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state, so another approach can be attempted without an environmental reset or human intervention.