# Episode: C0098

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot lifts the spoon on both attempts (frames 88–121 and 313–350, image and left_ego_image), but neither transfer succeeds. The first drop leaves the spoon on the tabletop (frames 136–144, all three cameras). After reacquisition, the spoon falls outside the drawer and past the table edge (frames 375–382, image); wrist_image shows the gripper empty afterward. This is visibly failed placement, not merely unconfirmed completion; the spoon's final resting location is outside the supplied views.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 136 | No |
| 136 | 164 | Yes |
| 164 | 375 | No |
| 375 | 383 | Yes |
| 383 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 136-164
- Categories: grasp
- Explanation: The carried spoon slips downward out of the gripper near the drawer at frames 136–138 and lands on the tabletop by frame 144 (image, left_ego_image, and wrist_image). The empty gripper continues into the drawer area and opens at frames 151–155 rather than depositing the spoon, before withdrawing to recover.
- Recovery: Return to the spoon's visible tabletop location, reacquire a secure grasp, verify retention with a small lift, and align the entire spoon over the drawer before releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon lands on the table without visible damage or disruption to other objects (frames 143–144, image and left_ego_image).
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop, so the robot can retry without environmental resetting or human intervention.

### Failure 2

- Frames: 375-383
- Categories: grasp
- Explanation: During the second transfer, the spoon leaves the gripper outside the drawer at frames 375–377 (wrist_image and image), falls toward the front table edge, and passes below it at frames 379–382 (image). The spoon is not retained until safely inside the drawer; the images do not establish why retention was lost.
- Recovery: Stop the transfer and have a person locate, inspect, and return the fallen spoon to an accessible tabletop position before retrying with a verified grasp and drawer alignment.
- Severity: low
- Severity evidence: The visible consequence is a fallen spoon and failed placement; no breakage or damage to other objects is shown, although the landing itself is out of view.
- Resetability: minor_reset
- Resetability evidence: Retrieval and replacement of the spoon are needed because it fell below the table and outside the visible workspace; this appears to be a straightforward human reset, though its exact resting location is unknown.