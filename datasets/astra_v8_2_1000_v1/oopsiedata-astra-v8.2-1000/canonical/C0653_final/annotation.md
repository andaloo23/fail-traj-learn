# Episode: C0653

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the upper drawer, but its gripper closes without securing the handle and then withdraws empty (frames 91–130, wrist_image and image). The drawer fronts remain closed, with no visible outward drawer travel through frame 194 (left_ego_image). This is a visibly unsuccessful acquisition attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 91 | No |
| 91 | 131 | Yes |
| 131 | 195 | No |

## Failure annotations

### Failure 1

- Frames: 91-131
- Categories: grasp
- Explanation: The fingers close near the upper drawer front without enclosing its silver handle (frames 91–100, wrist_image). The robot subsequently withdraws with an empty gripper while the handle and drawer remain in place (frames 108–130, wrist_image, image, and left_ego_image), establishing failed acquisition rather than a successful pull.
- Recovery: Reopen the gripper, realign the fingers around the drawer handle, and verify secure engagement before pulling along the drawer’s opening direction; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed; no damage or displacement of unrelated objects is visible in image or left_ego_image.
- Resetability: immediate
- Resetability evidence: The cabinet and handle remain in their original usable state, so another aligned grasp can be attempted without environmental resetting.