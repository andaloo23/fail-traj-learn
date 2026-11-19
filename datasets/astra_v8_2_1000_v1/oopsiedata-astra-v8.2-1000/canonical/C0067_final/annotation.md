# Episode: C0067

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The drawers are closed at frame 0 in left_ego_image and remain closed at frame 375. In wrist_image, the gripper closes near the drawer face around frames 107–119, then withdraws empty through frame 134 without opening it. After further empty gripper motions, it approaches the cabinet again in frames 281–375. The final attempt is unfinished, so its eventual outcome is unconfirmed; the earlier unsuccessful attempt is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 107 | No |
| 107 | 270 | Yes |
| 270 | 376 | No |

## Failure annotations

### Failure 1

- Frames: 107-270
- Categories: grasp
- Explanation: In wrist_image at frames 107–119, the fingers close near the drawer face without capturing the visible handle. The gripper subsequently moves away empty in frames 120–134 while left_ego_image shows the drawer remaining closed. Further finger opening and closing away from the handle, visible around frames 150–157, 181–183, and 230–237, does not establish acquisition or advance drawer opening. This unsuccessful sequence ends when the robot begins returning toward the cabinet.
- Recovery: Reposition the open gripper around the drawer handle, confirm that the handle is captured, and pull along the drawer’s sliding direction while monitoring drawer movement; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The drawer does not open, but image and left_ego_image show no visible damage, displaced tabletop objects, or meaningful damage risk from this failed acquisition.
- Resetability: immediate
- Resetability evidence: The cabinet and surrounding objects remain in place; another handle-acquisition attempt requires robot repositioning but no environmental reset or human intervention.