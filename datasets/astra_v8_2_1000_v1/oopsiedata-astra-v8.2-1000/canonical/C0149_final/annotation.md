# Episode: C0149

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the drawer cabinet but does not visibly open a drawer. In wrist_image, frames 101–125 show the fingers closing away from the silver handle and withdrawing empty; further finger cycling occurs through frame 224. In left_ego_image, the drawer fronts remain closed at frames 0, 125, and 224. This is a visibly unsuccessful acquisition attempt, not merely unconfirmed completion at the recording boundary.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 101 | No |
| 101 | 225 | Yes |

## Failure annotations

### Failure 1

- Frames: 101-225
- Categories: grasp
- Explanation: In wrist_image, frames 101–105 show the fingers closing beside the drawer front without enclosing the silver handle; frames 113–125 show the closed gripper moving away empty while the handle remains on the cabinet. The robot subsequently opens and closes its fingers in the same general area, including frames 145–150 and 169–175, without acquiring the handle or opening the drawer. left_ego_image confirms no drawer extension through frame 224. These repeated ineffective acquisition motions do not advance the task; no hidden cause is established.
- Recovery: Reopen the gripper, reposition so the fingers straddle the actual drawer handle, and verify acquisition before pulling along the drawer’s sliding direction. No human intervention is visibly required.
- Severity: low
- Severity evidence: The drawer remains closed and the attempt is unsuccessful; no damage, displaced tabletop objects, or meaningful damage risk is visible in image or left_ego_image through frame 224.
- Resetability: immediate
- Resetability evidence: The cabinet and surrounding objects remain in place, so another properly aligned attempt can proceed without an environmental reset or human intervention.