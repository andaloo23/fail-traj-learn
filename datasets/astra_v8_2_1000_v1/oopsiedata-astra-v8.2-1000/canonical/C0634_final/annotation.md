# Episode: C0634

## Episode annotation

- Language task: Open the drawer.
- Success label: success but suboptimal
- Outcome evidence: The upper drawer is initially closed (frame 0, left_ego_image). Two unsuccessful handle acquisitions precede the successful pull: wrist_image shows the gripper withdrawing without the handle at frames 81–97 and 142–144 while the drawer remains closed in left_ego_image. The upper drawer visibly extends at frames 200–214 and remains open after release and withdrawal through frame 254 (image and left_ego_image). No unintended object displacement or damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 78 | No |
| 78 | 98 | Yes |
| 98 | 139 | No |
| 139 | 145 | Yes |
| 145 | 255 | No |

## Failure annotations

### Failure 1

- Frames: 78-98
- Categories: grasp
- Explanation: Following finger closure near the upper drawer handle, the gripper begins withdrawing at frame 78 and is visibly separated from the handle by frame 81; it continues away empty through frame 97 (wrist_image). The upper drawer remains closed (left_ego_image), establishing unsuccessful acquisition rather than a completed opening.
- Recovery: Reopen the fingers, realign them around the handle, and verify a secure acquisition before pulling along the drawer travel direction; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt fails to open the drawer, but no damage or disturbance to surrounding objects is visible.
- Resetability: immediate
- Resetability evidence: The drawer and handle remain in place and available for another attempt without environmental intervention.

### Failure 2

- Frames: 139-145
- Categories: grasp
- Explanation: After the next closure near the handle, the gripper again moves away without retaining it during frames 139–144 (wrist_image); the handle separates from the fingers and the drawer remains closed in left_ego_image. Finger reopening at frame 145 begins another recovery.
- Recovery: Adjust the finger placement to capture the handle securely, confirm engagement, and then make a controlled outward pull; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Only another unsuccessful acquisition is visible; there is no observed damage or meaningful disruption.
- Resetability: immediate
- Resetability evidence: No scene reset is necessary because the drawer remains closed and accessible, with its handle intact.