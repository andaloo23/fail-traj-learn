# Episode: C0993

## Episode annotation

- Language task: Pick up NIST rod and insert into corresponding hole on the NIST board.
- Success label: failure
- Outcome evidence: The robot grasps and lifts the upright rod in frames 13–17 (side, wrist), but the rod leaves the grasp and falls onto the board in frames 21–23 (side, wrist). The robot subsequently approaches the fallen rod in frames 27–32 (side, wrist); no completed reacquisition or insertion is visible. This is a visibly failed insertion attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 21 | No |
| 21 | 24 | Yes |
| 24 | 33 | No |

## Failure annotations

### Failure 1

- Frames: 21-24
- Categories: grasp
- Explanation: After the rod is lifted and moved over the board, it shifts out of the fingers at frame 21, tips at frame 22, and lies horizontally on the board at frame 23 (side, wrist). Retention is lost before successful insertion; the images do not establish whether this was an unintended release or slipping.
- Recovery: Reapproach the fallen rod, establish a secure grasp, lift and orient it, then align with the corresponding hole before inserting and releasing. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The rod falls onto the board and remains accessible (side, frames 23–32); no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The rod remains on the accessible board surface and can be reacquired without environmental repair or human resetting; the robot begins approaching it again in frames 24–32 (side, wrist).