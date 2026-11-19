# Episode: C0236

## Episode annotation

- Language task: Place the black spoon in the sink.
- Success label: failure
- Outcome evidence: The black spoon lies on the counter beside the sink in frame 0 (left). The robot approaches its handle, but repeated finger closures and small withdrawals do not lift it (frames 19–74, left and wrist). At frame 74 (left), the spoon remains outside the sink; this is a visibly unsuccessful acquisition sequence, not merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 19 | No |
| 19 | 75 | Yes |

## Failure annotations

### Failure 1

- Frames: 19-75
- Categories: grasp
- Explanation: The fingers close near the spoon handle in frames 19–20, then withdraw empty in frame 21 while the spoon remains on the counter (left and wrist). Further closures and small withdrawals repeat around the same handle position, including frames 31–35, 49–52, and 65–69, without acquisition; the spoon remains on the counter through frame 74. This continuous ineffective grasping sequence does not advance transport to the sink; the underlying cause is not visible.
- Recovery: Stop repeating the same closure, reposition the open fingers to straddle the handle, and verify a secure grasp with a small lift before transporting the spoon over the sink and releasing it; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The spoon remains on the counter, with no visible damage, spill, or harmful displacement in left or wrist through frame 74.
- Resetability: immediate
- Resetability evidence: The spoon and sink remain available in their original usable state; another properly aligned attempt requires no environmental reset or human intervention.