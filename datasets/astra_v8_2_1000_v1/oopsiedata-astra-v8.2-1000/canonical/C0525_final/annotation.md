# Episode: C0525

## Episode annotation

- Language task: Stack and pack the cups.
- Success label: failure
- Outcome evidence: In base_image, the robot separates the initially nested cups (frames 62–110), forms a small stack (frames 170–177), and then attempts to nest them again (frames 243–288). The final placement tips and separates (frames 289–300), leaving a cup on its side beside the remaining upright cup arrangement through frame 315. This is a visibly failed final packing attempt, not merely unconfirmed completion; no separate packing container is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 289 | No |
| 289 | 304 | Yes |
| 304 | 316 | No |

## Failure annotations

### Failure 1

- Frames: 289-304
- Categories: manipulation
- Explanation: In base_image, the released upper cup is visibly tilted as the left gripper withdraws at frames 289–291. It continues tipping at frames 294–297, falls sideways onto the table at frame 298, and rolls away through frames 300–303. The placement does not produce a stable nested arrangement, preventing completion of packing.
- Recovery: Reacquire the sideways cup, orient it consistently with the remaining cups, align their axes, and lower it into a stable nested position before releasing; human intervention is not evidently necessary.
- Severity: low
- Severity evidence: The cup topples onto the clear tabletop; no damage, spilled contents, or meaningful damage risk is visible in base_image frames 298–315.
- Resetability: minor_reset
- Resetability evidence: The sideways cup remains accessible on the table and needs straightforward repositioning and reorientation, with no repair or difficult retrieval required.