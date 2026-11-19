# Episode: C0829

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the upper drawer handle, but withdraws with an empty gripper after its first closure (frames 84–115, wrist_image). Subsequent repeated finger movements do not open the drawer; its front remains flush with the cabinet through frame 361 (left_ego_image, wrist_image). This is a visibly unsuccessful acquisition sequence, not merely unconfirmed completion at the recording end.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 93 | No |
| 93 | 116 | Yes |
| 116 | 151 | No |
| 151 | 362 | Yes |

## Failure annotations

### Failure 1

- Frames: 93-116
- Categories: grasp
- Explanation: Following closure near the handle at frames 84–92, the gripper retreats without the handle between its fingers (frames 93–115, wrist_image). The drawer stays closed in left_ego_image, establishing unsuccessful acquisition rather than a successful pull.
- Recovery: Reopen the fingers and align them around the handle with sufficient clearance before closing and making a controlled outward pull; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed, with no visible damage or disturbance to surrounding objects.
- Resetability: immediate
- Resetability evidence: The handle and cabinet remain in place and available for another attempt without environmental resetting.

### Failure 2

- Frames: 151-362
- Categories: grasp
- Explanation: After approaching again, the fingers repeatedly close and reopen beside the handle without securing it (frames 151–158, 176–183, 201–208 and 226–233, wrist_image). Similar ineffective cycling continues through frames 326–333, followed by movement away from the handle through frame 361; left_ego_image shows no drawer opening throughout this interval.
- Recovery: Stop repeating the same closure, withdraw slightly, and realign the finger gap around the handle before retrying a gentle pull after confirming engagement; no human intervention is established as necessary.
- Severity: low
- Severity evidence: Repeated unsuccessful acquisitions prevent task completion, but no breakage, cabinet displacement or damage to nearby objects is visible.
- Resetability: immediate
- Resetability evidence: The drawer remains closed and its handle accessible; another properly aligned attempt requires no visible scene reset.
