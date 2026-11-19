# Episode: C0242_W02

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisional for this window: no toy is placed on the plate. overhead_cam and wrist_cam show approaches near the blue toy at frames 374–385 and 533–549, followed by empty retreats and prolonged movement or waiting away from the toys. At frames 657 and 699, wrist_cam shows all three toys outside the empty plate; overhead_cam confirms no placement. These unproductive withdrawals are visible, but a completed grasp attempt or unwanted collision is not clearly established. Earlier context beyond frames 348–349 and later execution are unavailable, so eventual completion remains unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 386 | No |
| 386 | 475 | Yes |
| 475 | 550 | No |
| 550 | 638 | Yes |
| 638 | 700 | No |

## Failure annotations

### Failure 1

- Frames: 386-475
- Categories: task_not_attempted
- Explanation: After approaching the blue toy, the empty gripper reverses away starting at frame 386. overhead_cam frames 390–435 show withdrawal toward the robot base, with a brief back-and-forth excursion around frames 402–418; wrist_cam confirms empty fingers and the toys left on the table. Frames 436–474 show prolonged waiting and small adjustments away from the targets rather than acquisition or placement. Together this is sustained unproductive behavior, not merely a brief alignment pause. No completed finger closure around the toy is clearly visible, so failed grasp is not asserted. A renewed workspace approach begins at frame 475.
- Recovery: Select a toy, approach with clearance from the plate and neighboring toys, align the fingers around a graspable portion, and verify retention with a short lift before transport; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is lost task progress; no object damage, disruptive contact, or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The toys and plate remain accessible on the tabletop, with no environmental resetting required.

### Failure 2

- Frames: 550-638
- Categories: task_not_attempted
- Explanation: Following another approach near the blue toy in overhead_cam and wrist_cam frames 533–549, the robot again withdraws empty from frame 550 onward. overhead_cam frames 562–613 show movement away from the toys toward the base, while wrist_cam shows no retained object. Frames 614–637 show sustained waiting there with the plate still empty and toys unmoved. This abandoned approach and prolonged absence of task-directed action do not advance placement; the images do not establish a completed failed acquisition or self-collision. Repositioning back toward the workspace begins at frame 638.
- Recovery: Resume a deliberate collision-free approach to one toy, correct the finger alignment before closing, and verify possession before moving toward the plate; no human intervention is visibly required.
- Severity: low
- Severity evidence: No damage or displaced scene component is visible; the supported consequence is another interval without task progress.
- Resetability: immediate
- Resetability evidence: No cleanup, replacement, or object repositioning is needed before another attempt because the tabletop arrangement remains usable.