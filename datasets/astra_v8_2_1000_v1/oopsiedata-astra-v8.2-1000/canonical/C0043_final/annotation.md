# Episode: C0043

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The wooden spoon is lifted but falls back onto the table twice, at frames 92–97 and 195–202 in wrist_image and left_ego_image. At frame 374, image and left_ego_image still show the spoon on the tabletop, while wrist_image shows the gripper handling the separate green object. The spoon is visibly not in the drawer; this is an observed unsuccessful episode, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 92 | No |
| 92 | 98 | Yes |
| 98 | 195 | No |
| 195 | 203 | Yes |
| 203 | 331 | No |
| 331 | 375 | Yes |

## Failure annotations

### Failure 1

- Frames: 92-98
- Categories: grasp
- Explanation: After lifting the spoon, the robot loses retention: its handle slides down out of the fingers at frames 92–94 in wrist_image, and the spoon falls onto the table and settles by frame 97 in left_ego_image. This interrupts transport toward the drawer.
- Recovery: Reapproach the spoon at its updated position, grasp farther along the handle with secure opposing contact, and verify retention with a small lift before transport; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon falls a short distance onto the tabletop; no damage or consequential disturbance of other objects is visible.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the table and can be grasped again without environmental resetting.

### Failure 2

- Frames: 195-203
- Categories: grasp
- Explanation: During the second lift, the spoon again slides downward relative to the fingers at frames 195–198 in wrist_image, separates from the gripper, and lands on the tabletop by frames 200–202 in left_ego_image. The robot again fails to retain it for placement.
- Recovery: Reassess the handle contact location and finger alignment, acquire a more secure grasp, and check that the spoon stays fixed during a low test lift before moving toward the drawer; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon returns to the tabletop with no visible breakage, spill, or meaningful damage.
- Resetability: immediate
- Resetability evidence: The dropped spoon remains within the visible workspace and available for another attempt without human resetting.

### Failure 3

- Frames: 331-375
- Categories: sequencing_semantic
- Explanation: The robot aligns with and descends toward the separate green elongated object at frames 331–348, then closes its fingers around it at frames 360–364 in wrist_image. Meanwhile, left_ego_image and image show the wooden spoon remaining on the table through frame 374. This wrong-object acquisition does not advance putting the spoon in the drawer; no physical grasp failure of the green object is established.
- Recovery: Release the green object safely onto the table, return to the visibly distinct wooden spoon, and securely grasp and place that spoon in the open drawer; no human intervention appears necessary.
- Severity: low
- Severity evidence: The wrong object is contacted and grasped, but no damage or hazardous displacement is visible.
- Resetability: immediate
- Resetability evidence: No damaged or inaccessible scene state is shown; the robot can safely release the green object and reattempt the task without human intervention.