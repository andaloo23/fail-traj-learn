# Episode: C0640

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary, frames 0 and 99 show the left blue-and-white stuffed toy remaining on the table and the largest, central white bowl remaining empty. After a small initial gripper movement in frames 3–5, the robot stays above the bowl without approaching or acquiring the toy through frame 99. The visible failure is sustained lack of task progress, not a failed grasp or an inferred abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 5 | No |
| 5 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 5-100
- Categories: task_not_attempted
- Explanation: In image_primary, frames 5–99 show the empty gripper remaining nearly stationary above the white bowl, with only minor positional changes and no approach to the left stuffed toy. The toy remains unchanged on the table throughout this approximately 19-second interval, establishing sustained unproductive behavior rather than a brief ordinary pause.
- Recovery: Resume task-directed motion by safely clearing the bowl, approaching and grasping the left blue-and-white toy, then transferring and releasing it into the largest white bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: No object displacement, damage, or meaningful damage risk is visible in image_primary, frames 5–99; the consequence is lack of task completion.
- Resetability: immediate
- Resetability evidence: The toy and bowls remain in their original usable positions, so another attempt requires no environmental reset or human intervention.