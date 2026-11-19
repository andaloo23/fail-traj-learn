# Episode: C0299

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the upper drawer handle and closes its gripper near it (frames 101–110, wrist_image), then withdraws without opening the drawer (frames 120–146, wrist_image and left_ego_image). The drawer fronts remain closed through frame 175 in left_ego_image. This is a visibly unsuccessful acquisition-and-pull attempt, not merely unconfirmed completion at recording end.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 120 | No |
| 120 | 176 | Yes |

## Failure annotations

### Failure 1

- Frames: 120-176
- Categories: grasp
- Explanation: After closing near the upper drawer handle, the gripper moves away while the handle and drawer remain in place (frames 120–130, wrist_image and left_ego_image). It continues withdrawing empty and subsequently opens its fingers (frames 140–175, wrist_image); no drawer opening results. The images establish failed acquisition, but not its hidden cause.
- Recovery: Reposition the open gripper around the handle, confirm secure engagement, and pull along the drawer’s travel direction while monitoring drawer movement; no human intervention is visibly required.
- Severity: low
- Severity evidence: The drawer remains closed, with no visible damage, displaced table objects, or other harmful consequences in image and left_ego_image through frame 175.
- Resetability: immediate
- Resetability evidence: The cabinet and surrounding objects remain in their original usable state; another handle-acquisition attempt requires no environmental reset or human intervention.