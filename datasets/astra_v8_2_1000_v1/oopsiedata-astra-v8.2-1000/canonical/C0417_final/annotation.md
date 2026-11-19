# Episode: C0417

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The drawer remains closed in image and left_ego_image at frames 0, 125, 250, and 399. The robot approaches the cabinet, closes its gripper, and withdraws without opening the drawer (frames 100–135, wrist_image and image), then repeatedly moves its empty gripper away from the handle. A later return toward the cabinet does not visibly complete opening before frame 399; that final attempt is unconfirmed rather than evidence of abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 104 | No |
| 104 | 136 | Yes |
| 136 | 314 | Yes |
| 314 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 104-136
- Categories: grasp
- Explanation: The fingers close near the cabinet face at frames 104–108 in wrist_image, then the arm withdraws with an empty gripper through frames 110–135. The drawer stays closed in image and left_ego_image, establishing a missed acquisition rather than a successful handle pull.
- Recovery: Reopen the gripper, realign its fingers around the drawer handle, and verify engagement before pulling along the drawer travel direction; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt does not open the drawer, but no damage or displacement of surrounding objects is visible.
- Resetability: immediate
- Resetability evidence: The cabinet and surrounding scene remain unchanged, so another aligned attempt requires no environmental reset.

### Failure 2

- Frames: 136-314
- Categories: task_not_attempted
- Explanation: After withdrawing, the robot repeatedly opens and closes its empty fingers and makes small movements away from the drawer handle, visible in wrist_image at frames 136–213 and image through frame 313. This sustained activity produces no drawer engagement or opening; left_ego_image shows the cabinet unchanged.
- Recovery: Stop cycling the empty gripper and return to a handle-directed approach, using the visible cabinet and handle to align a new grasp; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is prolonged lack of progress, with no observed damage, spill, or unintended object displacement.
- Resetability: immediate
- Resetability evidence: No scene restoration is needed; the robot can reposition and retry from the unchanged closed-drawer state.