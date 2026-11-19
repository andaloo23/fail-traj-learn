# Episode: C0210

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The drawer remains closed in left_ego_image at frames 0, 140 and 245. The gripper approaches the upper handle and closes near it at frames 84–92, but subsequently withdraws without opening the drawer (wrist_image, frames 94–140). Further repositioning and finger closure occur through frame 245 without visible opening. Thus an earlier acquisition visibly fails, while completion of the final attempt is unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 94 | No |
| 94 | 141 | Yes |
| 141 | 246 | No |

## Failure annotations

### Failure 1

- Frames: 94-141
- Categories: grasp
- Explanation: Following closure near the upper drawer handle at frames 84–92, the gripper moves away empty beginning at frame 94; the handle becomes increasingly separated from the fingers in wrist_image through frames 105–140. The drawer remains closed in left_ego_image. This establishes unsuccessful handle acquisition rather than a successful grip followed by a failed pull.
- Recovery: Reopen the fingers, realign them around the handle with sufficient clearance, and verify acquisition before pulling along the drawer’s travel direction; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed, with no visible damage, cabinet displacement or disturbance of the tabletop objects in image and left_ego_image.
- Resetability: immediate
- Resetability evidence: The handle and cabinet remain in place and accessible; another aligned grasp can be attempted without an environmental reset.