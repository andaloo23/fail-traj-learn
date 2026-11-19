# Episode: C0455

## Episode annotation

- Language task: stack the cups
- Success label: failure
- Outcome evidence: Three separate purple cups are visible at frame 0 in head. The left gripper lifts one cup and nests it into the central cup by frames 139–150 (head, left_wrist). The right gripper then carries the remaining cup toward that stack, but its release at frames 235–240 misses the opening; the cup topples and rolls across the tabletop (head, right_wrist). At frame 278, the two-cup stack remains upright and the third cup lies separately on its side. This is a visibly failed final stacking attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 235 | No |
| 235 | 279 | Yes |

## Failure annotations

### Failure 1

- Frames: 235-279
- Categories: manipulation
- Explanation: After successfully acquiring and transporting the third cup, the right gripper releases it without seating it in the existing stack at frames 235–240 (head, right_wrist). The cup falls beside the stack, tips onto its side, and rolls toward the near-right tabletop area through frames 242–264; it remains separate at frame 278. The placement therefore fails to complete the stack.
- Recovery: Reacquire the sideways cup, bring it upright, align its base directly over the stack opening, and lower it until securely nested before releasing. Human intervention is not inherently needed if the cup remains safely reachable; otherwise, a person should reposition it.
- Severity: low
- Severity evidence: The cup topples and rolls on the tabletop, but no breakage, spill, or damage to other objects is visible; the existing stack stays upright.
- Resetability: minor_reset
- Resetability evidence: The displaced cup needs to be retrieved and reoriented for another placement attempt. It remains visible on the tabletop at frame 278, supporting a straightforward reset rather than repair or difficult retrieval.