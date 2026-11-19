# Episode: C0238

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The spoon remains on the tabletop in image and left_ego_image from frame 0 through frame 317. The robot makes small positioning movements but then hovers without acquiring or transporting the spoon; wrist_image also shows an empty gripper. The task is visibly incomplete, with sustained unproductive behavior rather than an unconfirmed placement or a demonstrated failed grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 28 | No |
| 28 | 318 | Yes |

## Failure annotations

### Failure 1

- Frames: 28-318
- Categories: task_not_attempted
- Explanation: Following initial positioning, the robot remains hovering with only small adjustments and no discernible progress toward acquiring the spoon or using the drawer. Frames 28, 100, 180, 250 and 317 in image and left_ego_image show the spoon unchanged on the table; wrist_image shows no spoon acquisition. This extended unproductive interval is sustained stalling, not a completed failed grasp. Its underlying cause is not visible.
- Recovery: Re-localize the spoon and drawer, align the gripper with the spoon, acquire it and verify possession before transferring it into the accessible drawer. No environmental human intervention is visibly needed.
- Severity: low
- Severity evidence: The task remains incomplete, but no object displacement, damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop and the scene is unchanged, so another attempt requires no physical reset.