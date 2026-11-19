# Episode: C0728

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the spoon during frames 0–27, but the spoon remains on the tabletop throughout the episode, including frame 286 in image and left_ego_image. Frames 28–286 in wrist_image show prolonged hovering and small positional changes without visible acquisition or transfer to the drawer. The task is visibly uncompleted, with sustained unproductive behavior rather than merely an unconfirmed final placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 28 | No |
| 28 | 287 | Yes |

## Failure annotations

### Failure 1

- Frames: 28-287
- Categories: task_not_attempted
- Explanation: After the initial approach, the robot hovers near the spoon with small repeated positional changes but no discernible progress toward acquiring or placing it. Frames 28, 100, 170, 220 and 286 in image and left_ego_image show the spoon remaining in the same tabletop location; wrist_image shows the empty fingers nearby. This prolonged interval establishes sustained stalling, but does not establish a completed failed grasp or a hardware malfunction.
- Recovery: Re-localize the spoon, align the open fingers around a graspable section, descend and acquire it, then verify retention before transferring it into the drawer. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The spoon and surrounding objects remain on the table without visible damage, displacement or meaningful damage risk; the consequence is lack of task progress.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop and the scene requires no visible restoration before another attempt.