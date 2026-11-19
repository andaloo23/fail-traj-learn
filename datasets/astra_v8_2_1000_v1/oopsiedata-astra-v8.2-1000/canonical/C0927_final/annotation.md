# Episode: C0927

## Episode annotation

- Language task: stack the blue block on the yellow block
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the blue block in frames 25–27 and lowers it toward the yellow block in frames 41–45. The blue block tilts during placement and falls onto the table beside the yellow block by frame 52. Frames 60–69 show another approach, but no completed stack. This is a visibly failed placement followed by an unfinished recovery attempt.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 46 | No |
| 46 | 53 | Yes |
| 53 | 70 | No |

## Failure annotations

### Failure 1

- Frames: 46-53
- Categories: manipulation
- Explanation: In right_shoulder_cam, the previously held blue block visibly tilts at the edge of the yellow block starting at frame 46. During release and withdrawal through frames 51–52, it falls onto the table to the left instead of remaining stacked. The placement therefore fails despite successful initial acquisition and transport.
- Recovery: Reacquire the blue block from the table, align it fully over the yellow block, lower it into stable support, and release gently before withdrawing. No human intervention appears necessary.
- Severity: low
- Severity evidence: The blue block falls a short distance onto the tabletop and remains accessible; no damage or disruption to other scene objects is visible in right_shoulder_cam at frames 52–53.
- Resetability: immediate
- Resetability evidence: Both blocks remain upright and accessible on the table after the failed placement, allowing another attempt without environmental resetting or human intervention.