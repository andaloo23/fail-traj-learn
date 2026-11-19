# Episode: C0691

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary, frames 0 and 99 show the blue-and-white left stuffed toy remaining on the table and the largest, central white bowl empty. After a small initial gripper adjustment, the robot remains above the bowl without acquiring the toy throughout frames 3–99. The task visibly remains undone, with sustained inactivity rather than a failed grasp or merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 3 | No |
| 3 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 3-100
- Categories: task_not_attempted
- Explanation: In image_primary, frames 3–99 show the empty gripper remaining essentially stationary above the white bowl, with only slight positional variation; the left stuffed toy remains untouched on the table. This sustained interval does not advance acquisition or transfer of the toy. The images do not establish the cause of the inactivity.
- Recovery: Resume task-directed motion by approaching and grasping the blue-and-white left toy, then transfer it into the central white bowl and release it; no environmental human intervention is visibly needed.
- Severity: low
- Severity evidence: No object displacement, damage, or meaningful damage risk is visible; the consequence is lack of task progress.
- Resetability: immediate
- Resetability evidence: The toy and bowl remain in their original usable positions in image_primary through frame 99, so another attempt requires no visible environmental reset.