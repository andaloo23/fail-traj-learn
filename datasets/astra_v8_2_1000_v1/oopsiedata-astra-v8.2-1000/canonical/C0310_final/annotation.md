# Episode: C0310

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The drawer remains closed in left_ego_image at frames 0, 180, 300 and 347. The robot approaches its handle, makes repeated finger-closing motions nearby (wrist_image, frames 181–300), then withdraws without opening it (image and wrist_image, frames 306–347). This is a visibly unsuccessful attempt, rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 181 | No |
| 181 | 306 | Yes |
| 306 | 348 | No |

## Failure annotations

### Failure 1

- Frames: 181-306
- Categories: grasp
- Explanation: After approaching and aligning with the handle, the robot repeatedly closes and reopens its fingers without establishing an effective acquisition. In wrist_image, frames 181–190, 210–220, 255–263 and 284–305 show finger motions below or beside the horizontal handle; left_ego_image shows no drawer opening. The subsequent empty withdrawal in image and wrist_image, frames 306–347, confirms unsuccessful acquisition. Exact contact is partly obscured, so a hidden mechanical cause is not established.
- Recovery: Withdraw clear of the drawer front, realign the fingers around the handle with sufficient clearance, and verify a secure grasp before pulling along the drawer’s travel direction; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed, with no visible damage, displaced unrelated objects or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The cabinet and surrounding objects remain in place, so another aligned grasp attempt requires no environmental reset or human intervention.