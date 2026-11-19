# Episode: C0534

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The drawer remains closed during the approach and attempted acquisition (frames 0–129, left_ego_image and wrist_image). The gripper then withdraws without the handle or drawer following (frames 130–166, left_ego_image and wrist_image), and continues opening and closing away from the handle through frame 293. No drawer opening is visible; this is a visibly unsuccessful attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 102 | No |
| 102 | 294 | Yes |

## Failure annotations

### Failure 1

- Frames: 102-294
- Categories: grasp
- Explanation: At frames 102–108 in wrist_image, the fingers close beside the silver drawer handle rather than securely enclosing it. During frames 130–166, wrist_image shows the empty gripper moving away while left_ego_image shows the drawer remaining closed. Further finger opening and closing away from the handle (frames 180–293, wrist_image) produces no acquisition or opening. No secure handle possession is established.
- Recovery: Reopen the gripper, return to the handle, align the fingers around its accessible gripping surface, and verify acquisition before pulling along the drawer’s travel direction; no human intervention is visibly required.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed, with no visible damage, displaced surrounding objects, or meaningful damage risk in image and left_ego_image.
- Resetability: immediate
- Resetability evidence: The cabinet and surrounding objects remain in place; another correctly aligned acquisition can be attempted without an environmental reset or human intervention.