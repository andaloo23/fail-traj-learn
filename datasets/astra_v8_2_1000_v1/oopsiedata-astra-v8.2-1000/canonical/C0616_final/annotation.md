# Episode: C0616

## Episode annotation

- Language task: Pick up the yellow block and put it on the red block.
- Success label: failure
- Outcome evidence: The robot acquires and lifts the yellow block in frames 97–106, visible in wrist_cam and left_base_cam, and carries it toward the red block. During release in frames 193–203, the yellow block ends up on the tabletop beside the red block rather than on it. Frames 218–240 in wrist_cam, left_base_cam and right_base_cam confirm the blocks remain separate after the gripper withdraws; this is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 193 | No |
| 193 | 204 | Yes |
| 204 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 193-204
- Categories: manipulation
- Explanation: After carrying the yellow block to the red block, the gripper opens in frames 193–198 in wrist_cam. The yellow block moves down beside the red block and settles separately on the tabletop by frames 201–203, as visible in left_base_cam and right_base_cam. The release therefore fails to establish the requested stack; the images do not establish a hidden cause.
- Recovery: Reacquire the yellow block, lift it clear of the table, align it over a stable supporting surface of the red block, and lower it into supported contact before releasing; verify the stack after withdrawal. No human intervention is visibly required.
- Severity: low
- Severity evidence: The yellow block lands on the tabletop nearby; no damage or meaningful damage risk is visible, and the other objects remain usable.
- Resetability: immediate
- Resetability evidence: Both required blocks remain accessible on the tabletop, so the robot can reattempt without human resetting or cleanup.