# Episode: C0432

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary, frames 0–99, the blue-and-white left stuffed toy remains on the table and the largest, white bowl remains empty. The open, empty gripper slowly shifts rightward above the bowls without approaching or acquiring the toy. The task is visibly unachieved, with sustained nonproductive behavior rather than an unconfirmed placement or a failed grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 0-100
- Categories: task_not_attempted
- Explanation: Throughout image_primary frames 0–99, the gripper remains open and empty above the bowls, gradually shifting from above the white bowl toward the brown bowl (frames 0, 40, 68, and 99). It never approaches the left stuffed toy, and all objects remain stationary. This sustained interval shows no discernible acquisition attempt or productive progress toward moving the toy.
- Recovery: Approach the blue-and-white left toy, align and close the gripper around its body, verify acquisition, then lift and place it inside the largest white bowl. No human intervention is visibly needed.
- Severity: low
- Severity evidence: No object displacement, damage, or harmful contact is visible in image_primary frames 0–99; the consequence is lack of task progress.
- Resetability: immediate
- Resetability evidence: The toy and bowls remain in their original usable positions, so another attempt requires no environmental reset or human intervention.