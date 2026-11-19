# Episode: C0081

## Episode annotation

- Language task: Open the drawer.
- Success label: success but suboptimal
- Outcome evidence: The first handle acquisition fails: wrist_image shows the fingers closing beside the handle at frames 103–112 and withdrawing empty at frames 126–152 while the drawer remains closed in left_ego_image. After repositioning, the robot pulls the drawer outward at frames 239–258; image and left_ego_image show the extended drawer and exposed sides through frame 291. No unintended object displacement or damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 103 | No |
| 103 | 153 | Yes |
| 153 | 292 | No |

## Failure annotations

### Failure 1

- Frames: 103-153
- Categories: grasp
- Explanation: At frames 103–112 in wrist_image, the fingers close beside rather than around the drawer handle. The gripper subsequently withdraws empty at frames 126–152, with the handle remaining on the closed drawer in left_ego_image. This completed acquisition attempt does not open the drawer; the fingers begin reopening for another approach at frame 153.
- Recovery: Reopen the gripper, realign the fingers around the handle, establish a secure grasp, and pull along the drawer travel direction; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition delays opening, but no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The drawer and surrounding objects remain in place, so the robot can realign and retry without environmental resetting or human intervention.