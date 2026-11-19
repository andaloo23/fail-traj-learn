# Episode: C0278

## Episode annotation

- Language task: stack the cups
- Success label: failure
- Outcome evidence: Three separate upright cups are visible at frame 0 in head. The robot places the first lifted cup into the front cup, leaving a nested pair by frames 180–190 (head, right_wrist). It then lifts the remaining cup and brings it toward that pair (frames 246–310, head, left_wrist), but releases it off-center; it falls beside the pair and rolls across the table (frames 314–350, head, left_wrist). At frame 365, the pair remains upright and the third cup lies separately on its side (head). This is a visibly failed final placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 314 | No |
| 314 | 366 | Yes |

## Failure annotations

### Failure 1

- Frames: 314-366
- Categories: manipulation
- Explanation: After successfully carrying the remaining cup toward the nested pair, the robot releases it beside rather than securely into the receiving opening. At frame 314 it descends off-center, at frames 317–321 it tips onto the tabletop, and through frame 365 it remains separate from the stack (head, left_wrist). This failed placement prevents completion of the three-cup stack; no corrective action is visible.
- Recovery: Reacquire the fallen cup, orient it upright, align its base over the receiving cup opening, and lower it until securely nested before releasing. Human intervention is not evidently required.
- Severity: low
- Severity evidence: The cup falls onto and rolls along the tabletop without visible breakage, spilled contents, or damage to other objects (head, frames 319–365).
- Resetability: minor_reset
- Resetability evidence: The fallen cup remains accessible on the table and needs straightforward retrieval and reorientation; no repair or substantial environmental reset is visibly necessary.