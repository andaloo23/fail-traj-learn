# Episode: C0777

## Episode annotation

- Language task: stack the cups
- Success label: failure
- Outcome evidence: Three separate upright cups are visible at frame 0 in head. The left gripper lifts one cup and brings it above another (frames 140–179, head and left_wrist), but its release produces tumbling rather than a stack (frames 182–205). The right gripper subsequently lifts another cup, then releases it beside/against the fallen cup (frames 270–315, head and right_wrist). At frame 333, head shows the cups still separate, with two lying on their sides; this is a visibly failed stacking attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 180 | No |
| 180 | 210 | Yes |
| 210 | 299 | No |
| 299 | 334 | Yes |

## Failure annotations

### Failure 1

- Frames: 180-210
- Categories: manipulation
- Explanation: The left gripper opens while the transported cup is above the receiving cup (frames 180–182, head and left_wrist). Instead of nesting, the released cup tips across the receiving cup and tumbles away, disturbing the receiving cup as well (frames 183–205, head, left_wrist and right_wrist). No stack forms; the receiving cup subsequently falls onto its side.
- Recovery: Reacquire and upright the displaced cups, then align a held cup concentrically with an upright receiving cup and lower it until seated before releasing; human intervention is not inherently needed.
- Severity: low
- Severity evidence: The cups tumble on the tabletop without visible breakage, spilled contents, or damage to surrounding objects.
- Resetability: minor_reset
- Resetability evidence: The displaced cups remain accessible on the table; straightforward repositioning and uprighting can restore a valid stacking setup.

### Failure 2

- Frames: 299-334
- Categories: manipulation
- Explanation: After successfully lifting the right-side cup, the robot lowers it toward the cup lying horizontally rather than establishing a stable nested placement (frames 299–309, head and right_wrist). It opens the gripper at frames 310–312; the released cup tips and rolls away while the horizontal cup is also displaced (frames 314–333, head and both wrist cameras). This second placement again fails to create a stack.
- Recovery: Retrieve and upright the fallen cups before retrying; retain control of the next cup until it is visibly seated inside an upright receiving cup. Human intervention is not required by the visible state.
- Severity: low
- Severity evidence: Two cups roll or slide across the tabletop, but no damage or spill is visible, and neither is shown falling off the table.
- Resetability: minor_reset
- Resetability evidence: The cups need simple retrieval and uprighting on the accessible tabletop; no repair or substantial environmental reset is visibly necessary.