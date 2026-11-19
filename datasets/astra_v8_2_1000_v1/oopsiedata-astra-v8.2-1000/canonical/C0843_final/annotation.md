# Episode: C0843

## Episode annotation

- Language task: pick up the cup on the table, and hang it on the mug tree.
- Success label: failure
- Outcome evidence: The pale yellow cup is acquired and lifted from the table (frames 140–193, left_wrist and right_wrist), then positioned beside a mug-tree peg. After the gripper opens (frames 411–417, left_wrist), the cup falls away rather than remaining hung (frames 426–440, left_wrist and right_wrist). At frame 497, head and right_wrist show the cup back on the tabletop and the gripper withdrawn; this is a visibly failed hanging attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 411 | No |
| 411 | 458 | Yes |
| 458 | 498 | No |

## Failure annotations

### Failure 1

- Frames: 411-458
- Categories: manipulation
- Explanation: The robot opens its gripper while placing the held cup beside the tree, but does not establish lasting support on the peg (frames 411–425, left_wrist). The cup falls away and settles on the table (frames 426–457, right_wrist; also visible in head), so the post-acquisition hanging operation fails. The precise handle-to-peg misalignment is not clear from the images.
- Recovery: Reacquire the cup from the tabletop, align its handle with an available peg, and lower it until the peg supports it before fully releasing and withdrawing; no human intervention is visibly required.
- Severity: low
- Severity evidence: The cup falls onto the tabletop, with no visible breakage, spill, or damage to the tree or surrounding objects.
- Resetability: immediate
- Resetability evidence: The cup remains accessible on the table and the tree remains standing; another acquisition and hanging attempt can proceed without an environmental reset.