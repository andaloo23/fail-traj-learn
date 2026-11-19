# Episode: C0037

## Episode annotation

- Language task: remove the blue cloth from the yellow block
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the gripper raises a pinched portion of the blue cloth through frames 43–52, but the cloth falls away at frame 53 and remains on the table as the gripper withdraws empty through frame 56. Frames 57–69 show a renewed approach without completed removal. The yellow block remains obscured, so its identity and final position cannot be independently verified; the visible attempt fails to retain the cloth, and subsequent completion is unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 53 | No |
| 53 | 57 | Yes |
| 57 | 70 | No |

## Failure annotations

### Failure 1

- Frames: 53-57
- Categories: grasp
- Explanation: In right_shoulder_cam, the cloth rises with the gripper at frames 50–52, then separates and collapses onto the table at frame 53. The gripper retreats empty through frame 56, losing retention before removing the cloth from the covered object.
- Recovery: Reapproach an accessible cloth fold or edge, secure a deeper pinch, and verify retention with a small lift before lifting and moving the cloth clear of the block; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The cloth falls back onto the tabletop with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The cloth remains accessible on the table and can be grasped again without an environmental reset or human intervention.