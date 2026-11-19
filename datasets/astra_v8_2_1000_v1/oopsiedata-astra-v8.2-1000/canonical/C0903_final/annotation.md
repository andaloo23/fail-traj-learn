# Episode: C0903

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The spoon remains on the tabletop throughout, including frames 0, 120, 212 and 235 in image and left_ego_image. The robot approaches its vicinity but later closes its fingers empty and lifts without the spoon (wrist_image, frames 166–212). No transfer into the drawer occurs; this is a visibly unsuccessful acquisition, not merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 52 | No |
| 52 | 151 | Yes |
| 151 | 212 | Yes |
| 212 | 236 | No |

## Failure annotations

### Failure 1

- Frames: 52-151
- Categories: task_not_attempted
- Explanation: After approaching the spoon, the robot spends an extended interval making small back-and-forth adjustments without acquiring it or meaningfully progressing toward the drawer. Frames 52, 80, 110 and 150 in image and left_ego_image show the spoon unchanged beside the gripper; wrist_image shows the spoon offset from the fingers. This sustained unproductive behavior exceeds a brief alignment pause.
- Recovery: Re-localize the spoon and align the open fingers around its handle before descending; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The task stalls, but no damage or meaningful damage risk is visible, and the tabletop objects remain in place.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop, so another properly aligned attempt requires no environmental reset.

### Failure 2

- Frames: 151-212
- Categories: grasp
- Explanation: The fingers repeatedly close and reopen over an empty tabletop location rather than enclosing the spoon (wrist_image, frames 151–180). The robot subsequently lifts away empty through frames 196–211, while image and left_ego_image show the spoon still lying on the table. These before-and-after observations establish failed acquisition.
- Recovery: Open the gripper, reposition over the visible spoon handle, and confirm that the spoon lifts with the fingers before transporting it to the drawer; no human intervention is visibly required.
- Severity: low
- Severity evidence: The unsuccessful grasp leaves the spoon on the table without visible damage or harmful displacement.
- Resetability: immediate
- Resetability evidence: No object retrieval, cleanup or repair is needed; the spoon remains available for a corrected grasp.