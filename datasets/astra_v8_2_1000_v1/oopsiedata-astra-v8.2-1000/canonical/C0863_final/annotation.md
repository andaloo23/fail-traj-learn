# Episode: C0863

## Episode annotation

- Language task: Stack all the bowls on the table into the middle bowl.
- Success label: failure
- Outcome evidence: Frame 0 in head shows separate orange, middle blue, and teal bowls. Frames 104–125 in head and right_wrist show the teal bowl placed into the middle blue bowl. The orange bowl is subsequently lifted and brought toward that stack, but is lowered and released beside it rather than into it (frames 194–219, head and left_wrist). At frame 233 in head, the orange bowl remains separate, establishing an unsuccessful placement rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 194 | No |
| 194 | 210 | Yes |
| 210 | 234 | No |

## Failure annotations

### Failure 1

- Frames: 194-210
- Categories: manipulation
- Explanation: After carrying the orange bowl toward the middle stack, the robot moves it to the left of the stack and lowers it onto the table instead of nesting it (frames 194–205, head and left_wrist). The gripper opens and leaves the orange bowl separate by frame 210; subsequent withdrawal confirms the failed placement in frames 219–233, head. Possession during transport is visible, but the reason for the placement offset is not established.
- Recovery: Regrasp the orange bowl, lift it clear of the table, align it above the middle stack, and lower it carefully into the teal bowl before releasing; verify that all three bowls are nested. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The orange bowl remains upright on the tabletop beside the stack, with no visible damage, spill, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The bowl remains accessible and the stack remains on the table; another placement attempt requires no environmental reset or human intervention.