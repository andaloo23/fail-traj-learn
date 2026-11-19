# Episode: C0246

## Episode annotation

- Language task: Pick up the green cup and stack it on the purple cup.
- Success label: failure
- Outcome evidence: camera_high and camera_wrist_right show the gripper approaching the green cup, then withdrawing without it during frames 169–204 and 284–355 while the cups remain separate. Further positioning and acquisition activity follows, but frames 583–599 in camera_high and camera_wrist_right do not show the green cup stacked on the purple cup. Completion is unconfirmed at the recording end, in addition to the earlier visibly failed acquisitions.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 169 | No |
| 169 | 205 | Yes |
| 205 | 284 | No |
| 284 | 356 | Yes |
| 356 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 169-205
- Categories: grasp
- Explanation: Following the acquisition attempt near frames 155–168, the gripper moves away empty during frames 169–204. camera_high shows the green cup remaining on the table, separate from the purple cup; camera_wrist_right shows the cup receding from the gripper rather than being carried. This fails to acquire the required cup.
- Recovery: Reopen the gripper, realign around the green cup, and verify a secure grasp with a small lift before transporting it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The cup remains on the tabletop, with no visible damage, spill, or harmful collision.
- Resetability: immediate
- Resetability evidence: Both cups remain available for another attempt without environmental resetting or human intervention.

### Failure 2

- Frames: 284-356
- Categories: grasp
- Explanation: After the renewed approach and gripper closure near frames 270–283, the gripper again withdraws without carrying the green cup during frames 284–355. camera_high shows the green cup remaining in its tabletop position, while camera_wrist_right shows changing separation between the cup and withdrawing gripper. The repeated acquisition does not advance stacking.
- Recovery: Return with the gripper open, correct the grasp alignment, and confirm that the green cup moves with the gripper before proceeding toward the purple cup; no human intervention is visibly needed.
- Severity: low
- Severity evidence: This attempt leaves the cups separate without visible damage or a meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The green cup remains accessible on the table and can be approached again without resetting the scene.