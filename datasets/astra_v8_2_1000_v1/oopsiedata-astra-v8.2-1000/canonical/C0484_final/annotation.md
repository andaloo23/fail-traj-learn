# Episode: C0484

## Episode annotation

- Language task: Stack all the bowls on the table into the middle bowl.
- Success label: failure
- Outcome evidence: Frame 0 in head shows separate teal, middle blue, and orange bowls. The right arm lifts the orange bowl but releases it beside the blue bowl rather than nesting it (frames 83–119, head and right_wrist). The left arm subsequently places the teal bowl into the blue bowl (frames 190–214, head and left_wrist). At frame 229, head still shows the orange bowl separate while right_wrist shows another approach toward it; completion is not observed, and the earlier orange placement visibly failed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 101 | No |
| 101 | 120 | Yes |
| 120 | 230 | No |

## Failure annotations

### Failure 1

- Frames: 101-120
- Categories: manipulation
- Explanation: After transporting the orange bowl toward the middle blue bowl, the right gripper opens while the orange bowl remains offset to the right (frames 101–106, head and right_wrist). The orange bowl settles beside the blue bowl, and both bowls visibly rock rather than form a stack as the empty gripper withdraws (frames 107–119, head). This is a failed placement after established object control, not a failed initial acquisition.
- Recovery: Allow the bowls to settle, reacquire the orange bowl, center it above the middle bowl or its nested stack, and lower it until supported before releasing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The bowls rock and shift on the tabletop, but remain accessible with no visible damage, spill, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: No environmental repair or manual reset is needed; the robot can observe the settled bowl positions and reattempt placement directly.