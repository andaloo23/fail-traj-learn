# Episode: C0123

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the drawer handle and closes its gripper near it (frames 48–91, wrist_image), but subsequently withdraws without pulling the drawer outward (frames 115–150, wrist_image and left_ego_image). The drawer remains closed as the arm moves farther away through frame 283 (image and left_ego_image). This is a visibly unsuccessful acquisition attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 115 | No |
| 115 | 284 | Yes |

## Failure annotations

### Failure 1

- Frames: 115-284
- Categories: grasp
- Explanation: After closing near the handle at frames 83–91, the gripper starts withdrawing empty at frame 115; by frames 124–150, wrist_image clearly shows separation from the handle while left_ego_image shows the drawer still closed. The robot continues moving away and opening and closing its empty fingers through frame 283 without reacquiring the handle or opening the drawer (wrist_image, image). The views establish failed acquisition but not its underlying cause.
- Recovery: Reorient and return to the handle, align the fingers around its accessible gripping surfaces, and verify secure engagement before pulling along the drawer’s travel direction; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The drawer is not opened, but no damage, displaced unrelated objects, or meaningful damage risk is visible in image or left_ego_image through frame 283.
- Resetability: immediate
- Resetability evidence: The cabinet and surrounding objects remain in place; another handle-acquisition attempt requires robot repositioning but no environmental reset or human intervention.