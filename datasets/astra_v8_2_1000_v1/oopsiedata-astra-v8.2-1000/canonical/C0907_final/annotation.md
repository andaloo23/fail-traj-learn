# Episode: C0907

## Episode annotation

- Language task: Open the drawer.
- Success label: success but suboptimal
- Outcome evidence: The first handle-acquisition attempt does not open the drawer: wrist_image shows the gripper moving away without the handle in frames 110–168, while left_ego_image shows the drawer remaining closed. After reapproaching, the robot pulls the upper drawer outward in frames 270–289; image and left_ego_image show the extended drawer remaining open through frame 327 after release. No unintended object displacement or damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 110 | No |
| 110 | 169 | Yes |
| 169 | 328 | No |

## Failure annotations

### Failure 1

- Frames: 110-169
- Categories: grasp
- Explanation: Following the initial acquisition attempt near the upper drawer handle, the gripper moves away empty starting at frame 110 in wrist_image, with clear separation by frames 127–168. The handle stays on the closed drawer, as confirmed by left_ego_image and image; this attempted withdrawal does not open it. The images do not establish a hidden mechanical or perception cause.
- Recovery: Reopen and realign the fingers around the handle, establish a secure grasp, then pull along the drawer’s sliding direction while checking drawer movement; no human intervention is needed.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed without visible damage, displaced surrounding objects, or a meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The cabinet and handle remain in place and usable, so another grasp can be attempted without environmental resetting or human intervention.