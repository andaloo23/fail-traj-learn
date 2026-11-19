# Episode: C0506

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the spoon and lowers its gripper beside the handle at frames 70–86 in image, left_ego_image and wrist_image. It then withdraws empty at frames 87–101 while the spoon remains on the tabletop. At frame 116, image and left_ego_image still show the spoon outside the drawer, establishing a failed acquisition rather than merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 87 | No |
| 87 | 117 | Yes |

## Failure annotations

### Failure 1

- Frames: 87-117
- Categories: grasp
- Explanation: Following the near-handle acquisition attempt at frames 76–86, the gripper begins withdrawing without the spoon at frame 87. Frames 90–101 in left_ego_image and wrist_image show increasing separation while the spoon stays on the table; image and left_ego_image confirm it remains there through frame 116. The attempted acquisition therefore fails to advance the spoon toward the drawer; the underlying cause is not visible.
- Recovery: Reposition the open gripper so its fingers straddle the spoon handle, lower carefully, close and verify possession with a small lift before transporting it into the open drawer; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The spoon remains on the tabletop, with no visible damage, dropped object or disruption to surrounding objects.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible in its original tabletop area, so another acquisition attempt requires no environmental reset or human intervention.