# Episode: C0023

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot grips and lifts the spoon in frames 89–104 (left_ego_image, wrist_image), but loses it in frames 105–108. The spoon settles on the tabletop by frame 114 and remains there through frame 204 (image, left_ego_image), while the robot moves toward the drawer empty-handed. This is a visibly failed transfer, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 105 | No |
| 105 | 205 | Yes |

## Failure annotations

### Failure 1

- Frames: 105-205
- Categories: grasp
- Explanation: Starting at frame 105, the spoon slides out of the lifting gripper; frames 107–108 show separation and its fall toward the tabletop (wrist_image, left_ego_image). By frame 114 it rests on the table. The robot continues away empty-handed toward the drawer rather than reacquiring it, and the spoon remains outside the drawer through frame 204 (image, left_ego_image). No recovery is visible.
- Recovery: Return to the spoon, align the fingers around its handle, reacquire it, and verify retention with a small lift before transporting it into the open drawer and releasing it. Human intervention is not visibly required.
- Severity: low
- Severity evidence: The spoon falls onto the tabletop and remains accessible; no damage or disruption to other objects is visible in frames 108–114 or 204 (left_ego_image).
- Resetability: immediate
- Resetability evidence: The spoon remains on the reachable tabletop, with no visible damage or cleanup requirement; another acquisition attempt can proceed without human resetting.