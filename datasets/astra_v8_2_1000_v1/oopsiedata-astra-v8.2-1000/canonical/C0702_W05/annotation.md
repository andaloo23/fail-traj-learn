# Episode: C0702_W05

## Episode annotation

- Language task: Stack and pack the cups.
- Success label: failure
- Outcome evidence: In base_image, frames 1400–1484 show the left gripper bringing a held cup toward the standing cups. During release at frames 1487–1509, that cup tips sideways rather than nesting successfully. Frames 1512–1628 show it rolling toward and eventually beyond the lower image boundary while the standing cups remain separate. This is a visibly failed placement, not merely unconfirmed completion. The label is provisional for this window; earlier execution is unavailable beyond the supplied context, and the cup’s eventual location outside the view is unknown.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1487 | No |
| 1487 | 1509 | Yes |
| 1509 | 1629 | No |

## Failure annotations

### Failure 1

- Frames: 1487-1509
- Categories: manipulation
- Explanation: In base_image at frame 1487, the cup begins tipping as the left gripper opens over the standing cups; by frames 1504–1508 it is falling sideways rather than remaining nested. Frame 1509 confirms the unsuccessful placement, with the released cup lying separately on the table. The subsequent withdrawal clears the objects; the cup’s continued rolling is a consequence of this placement rather than a separate failed action.
- Recovery: Locate the loose cup, reacquire and reorient it, then align it concentrically with the standing cups and verify stable nesting before releasing. Human assistance is needed only if its eventual location is outside the robot’s safe reachable workspace.
- Severity: low
- Severity evidence: The cup topples and rolls on the table in base_image, frames 1507–1618; no damage or spill is visible. Its disappearance below the image boundary does not establish a fall off the table or damage.
- Resetability: minor_reset
- Resetability evidence: The loose cup needs retrieval and reorientation before another placement attempt; this appears straightforward while it remains on the visible tabletop. Its final location beyond the lower image boundary is unknown, so additional retrieval difficulty cannot be established.