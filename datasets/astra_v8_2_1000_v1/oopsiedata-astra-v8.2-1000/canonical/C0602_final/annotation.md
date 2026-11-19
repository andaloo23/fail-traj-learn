# Episode: C0602

## Episode annotation

- Language task: Pick up the cup on the table, and hang it on the mug tree.
- Success label: failure
- Outcome evidence: The robot picks up the light-blue cup and lifts it toward the mug tree (frames 180–235, head and right_wrist), then makes extended positioning adjustments near the pegs. On release, the cup falls rather than remaining hung (frames 746–755, left_wrist and right_wrist). At frame 801, head and both wrist cameras show the cup on the tabletop beside the tree and the gripper withdrawn; this is a visibly failed hanging attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 746 | No |
| 746 | 769 | Yes |
| 769 | 802 | No |

## Failure annotations

### Failure 1

- Frames: 746-769
- Categories: manipulation
- Explanation: After carrying and positioning the cup near a peg, the robot releases it without establishing support on the tree. The cup separates from the open gripper and falls onto the table at frames 746–750, then tumbles away from the tree through frames 751–768 (left_wrist, right_wrist, and head). The intended hanging manipulation fails; the precise handle-to-peg misalignment is not fully visible.
- Recovery: Reacquire the cup from the tabletop, orient its handle around an available peg, and lower it until the peg visibly supports it before releasing and withdrawing. Human intervention is not visibly required.
- Severity: low
- Severity evidence: The cup falls and tumbles on the tabletop; no breakage, spill, or damage to the tree or other objects is visible.
- Resetability: immediate
- Resetability evidence: The cup remains accessible on the tabletop and the tree remains standing, allowing another acquisition and hanging attempt without a human reset.