# Episode: C0461

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: The blue toy is deposited on the plate at frames 200–207, and the pink toy at frames 695–703, in overhead_cam and wrist_cam. The tan toy remains on the table after an empty grasp and transfer motion (frames 348–498). At frame 771, both cameras show only the blue and pink toys on the plate, with the tan toy still outside it. Thus the task is visibly incomplete following a failed acquisition, not merely unconfirmed completion. No unwanted collision is clearly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 348 | No |
| 348 | 499 | Yes |
| 499 | 772 | No |

## Failure annotations

### Failure 1

- Frames: 348-499
- Categories: grasp
- Explanation: At frame 348 in wrist_cam, the fingers have closed short of the tan toy without enclosing it. At frames 353–370, overhead_cam shows the gripper lifting and moving away empty while the toy stays on the table. The robot continues an empty transfer toward the plate and opens its fingers at frames 488–498; wrist_cam again reveals the tan toy still on the table. This completed acquisition and empty transfer do not place the toy.
- Recovery: Re-localize the tan toy, open and align the fingers around its body, descend with table clearance, and verify acquisition with a small lift before transferring it to the plate. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy remains on the tabletop, and neither camera shows damage or consequential disturbance from the missed grasp.
- Resetability: immediate
- Resetability evidence: The tan toy remains accessible in its original area; another acquisition can be attempted without environmental resetting or human intervention.