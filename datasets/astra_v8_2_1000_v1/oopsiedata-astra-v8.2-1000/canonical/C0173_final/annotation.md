# Episode: C0173

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the upper drawer but repeatedly closes and withdraws its gripper without acquiring the handle (wrist_image, frames 90–110, 129–150, 170–190, 209–230 and 271–290). The drawers remain closed in left_ego_image through frame 399. This is a visibly unsuccessful acquisition sequence, not merely unconfirmed completion; no drawer opening or damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 90 | No |
| 90 | 291 | Yes |
| 291 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 90-291
- Categories: grasp
- Explanation: In wrist_image, the fingers repeatedly close beside or above the silver handle rather than securely around it, then withdraw empty while the handle stays in place; examples occur at frames 90–110, 129–150, 170–190, 209–230 and 271–290. These repeated near-handle acquisition misses never produce drawer motion, as corroborated by left_ego_image. No established handle possession is visible.
- Recovery: Open the gripper, reposition to straddle the accessible part of the handle with sufficient insertion depth, verify acquisition, and then pull along the drawer's travel direction; no human intervention is visibly required.
- Severity: low
- Severity evidence: The attempts fail to open the drawer, but left_ego_image and image show no visible damage, cabinet displacement or disturbance of nearby objects.
- Resetability: immediate
- Resetability evidence: The drawer and surrounding scene remain in their original usable state; another aligned acquisition attempt needs no environmental reset.

### Failure 2

- Frames: 291-400
- Categories: task_not_attempted
- Explanation: Following the last empty withdrawal, the open gripper remains near the cabinet without another acquisition or pull for the remainder of the episode, with only small pose changes (wrist_image, frames 291, 320, 350 and 399). The sustained lack of productive action leaves the drawer closed in left_ego_image.
- Recovery: Resume a deliberately realigned handle acquisition and controlled pull rather than continuing to hover; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The visible consequence is prolonged noncompletion only; no damage or concrete damaging interaction is shown during this interval.
- Resetability: immediate
- Resetability evidence: Nothing in the environment needs restoring before another attempt; the cabinet remains upright and the drawer closed.