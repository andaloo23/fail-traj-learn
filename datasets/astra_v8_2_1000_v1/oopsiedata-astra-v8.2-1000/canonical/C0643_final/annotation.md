# Episode: C0643

## Episode annotation

- Language task: pick up the cup on the table, and hang it on the mug tree.
- Success label: failure
- Outcome evidence: The robot lifts the light-blue cup and carries it toward the mug tree (frames 165–225, head and left_wrist). When the right gripper opens, the cup falls rather than remaining suspended (frames 340–355, right_wrist and left_wrist). It ends upright on the table beside the tree, with the gripper withdrawn (frames 385–405, head and both wrist cameras). This is a visibly failed hanging attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 340 | No |
| 340 | 370 | Yes |
| 370 | 406 | No |

## Failure annotations

### Failure 1

- Frames: 340-370
- Categories: manipulation
- Explanation: After successfully transporting the cup, the robot opens its gripper without securing the cup on a branch. The cup descends away from the branch in frames 340–355 (right_wrist and left_wrist) and settles on the tabletop beside the tree by frames 364–369 (left_wrist). The placement therefore fails to accomplish hanging; the precise handle-to-branch misalignment is not fully visible.
- Recovery: Reacquire the upright cup, align its handle with an available branch, and lower it until the branch supports it before releasing and withdrawing. No human intervention appears necessary.
- Severity: low
- Severity evidence: The cup falls a short distance onto the table and remains upright; no breakage, spill, or other meaningful damage is visible in frames 364–405.
- Resetability: immediate
- Resetability evidence: The cup remains accessible on the tabletop and the tree remains standing, so another acquisition and hanging attempt can begin without environmental resetting or human intervention.