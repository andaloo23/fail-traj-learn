# Episode: C0251_W05

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: success but suboptimal
- Outcome evidence: Provisionally for this window, the robot completes placement after an unsuccessful acquisition. In wrist_cam at frames 1440–1458, the fingers close near the pink rabbit, reopen, and withdraw empty while it remains outside the plate; overhead_cam corroborates its position. A subsequent grasp at frames 1489–1500 carries the rabbit onto the plate at frames 1511–1533. At frames 1538–1558, wrist_cam shows the released pink rabbit alongside the tan and blue toys on the plate. overhead_cam confirms the toys remain there through frame 1749 after withdrawal. No unwanted collision is clearly established. Earlier execution beyond the supplied context frames and later execution are unavailable, so this is not a whole-episode judgment.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1440 | No |
| 1440 | 1447 | Yes |
| 1447 | 1750 | No |

## Failure annotations

### Failure 1

- Frames: 1440-1447
- Categories: grasp
- Explanation: In wrist_cam at frames 1440–1446, the fingers briefly close beside the pink rabbit near the plate rim without securing it, then reopen. The empty withdrawal at frames 1447–1458 establishes failed acquisition rather than merely an unfinished closure; overhead_cam shows the rabbit remaining outside the plate. Proximity to the plate does not independently establish an unwanted collision.
- Recovery: Reposition the open fingers around the rabbit’s body with clearance from the plate, verify retention with a small lift, and transport it over the plate before release; no human intervention is needed.
- Severity: low
- Severity evidence: The unsuccessful acquisition leaves the toy on the tabletop with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The rabbit remains accessible beside the plate, and another attempt requires no environmental reset or human intervention.