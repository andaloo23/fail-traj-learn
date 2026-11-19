# Episode: C0213

## Episode annotation

- Language task: Open the drawer.
- Success label: success but suboptimal
- Outcome evidence: The robot makes two unsuccessful handle-acquisition attempts before opening the upper drawer. In wrist_image, the closed fingers withdraw without the handle at frames 96–108 and 184–198, while left_ego_image shows the drawer remaining closed. A later grasp succeeds: frames 301–318 in image and left_ego_image show the drawer sliding outward, exposing its sides and interior. It remains open after release through frame 373. No unintended object displacement or damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 96 | No |
| 96 | 133 | Yes |
| 133 | 184 | No |
| 184 | 208 | Yes |
| 208 | 374 | No |

## Failure annotations

### Failure 1

- Frames: 96-133
- Categories: grasp
- Explanation: After closing near the upper drawer handle, the fingers withdraw empty beginning at frame 96; wrist_image shows increasing separation from the handle through frame 108. The drawer stays closed in left_ego_image. Subsequent small finger movements away from the handle do not acquire it; reopening for another approach begins at frame 133.
- Recovery: Reopen the gripper, align the fingers around the handle with adequate engagement depth, and verify acquisition before pulling along the drawer’s travel direction; no human intervention is needed.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed, with no visible damage or disturbance to surrounding objects.
- Resetability: immediate
- Resetability evidence: The handle and cabinet remain in place and available for another attempt without environmental resetting.

### Failure 2

- Frames: 184-208
- Categories: grasp
- Explanation: Following a second closure near the handle at frames 171–178, the gripper withdraws without retaining it at frames 184–198 in wrist_image. The handle remains on the closed drawer in left_ego_image, establishing another failed acquisition rather than a successful pull. The next reopening and repositioning sequence begins at frame 208.
- Recovery: Reopen and reposition the fingers to securely surround the handle, confirm engagement, and then pull straight outward; no human intervention is needed.
- Severity: low
- Severity evidence: Only the acquisition attempt fails; no damage, cabinet displacement, or unrelated object disturbance is visible.
- Resetability: immediate
- Resetability evidence: The drawer remains closed and accessible, so another grasp can be attempted without human resetting.