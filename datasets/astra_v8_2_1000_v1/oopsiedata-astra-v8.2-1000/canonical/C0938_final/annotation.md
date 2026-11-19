# Episode: C0938

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The drawer remains closed in left_ego_image from frame 0 through frame 175. In wrist_image, the gripper closes near the silver handle at frames 79–81, then withdraws empty at frames 94–103 without pulling the drawer open. Later repositioning is visible at frames 117–175, but no completed opening is observed; this is a visibly failed acquisition followed by an unfinished retry.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 79 | No |
| 79 | 117 | Yes |
| 117 | 176 | No |

## Failure annotations

### Failure 1

- Frames: 79-117
- Categories: grasp
- Explanation: In wrist_image at frames 79–81, the fingers close near the end of the silver drawer handle without securing it. At frames 94–103 the closed gripper moves away empty while the handle remains on the closed drawer; left_ego_image confirms no drawer opening. The unsuccessful acquisition and withdrawal do not advance the task.
- Recovery: Reopen the gripper, realign the fingers around an accessible portion of the handle, establish a secure grasp, and pull along the drawer's travel direction while checking for opening. No human intervention is visibly required.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed, with no visible damage or disturbance to surrounding objects in image and left_ego_image through frame 117.
- Resetability: immediate
- Resetability evidence: The handle and cabinet remain in place and usable; another aligned grasp can be attempted without an environmental reset or human intervention.