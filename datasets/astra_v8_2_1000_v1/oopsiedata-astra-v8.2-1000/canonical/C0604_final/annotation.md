# Episode: C0604

## Episode annotation

- Language task: Pick up NIST rod and insert into corresponding hole on the NIST board.
- Success label: failure
- Outcome evidence: The rod remains upright near the board center throughout frames 0–66 in side. The robot lowers its gripper near the board’s right edge, closes without acquiring the rod, and withdraws empty (frames 52–66, side and wrist). This is a visibly unsuccessful acquisition attempt; no rod transport or insertion is observed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 52 | No |
| 52 | 67 | Yes |

## Failure annotations

### Failure 1

- Frames: 52-67
- Categories: grasp
- Explanation: In frames 52–56, side and wrist show the fingers closing on empty space near the board’s right edge rather than around the upright rod. The gripper subsequently rises empty in frames 58–66 while the rod remains stationary in side, establishing failed acquisition rather than merely an unfinished attempt.
- Recovery: Reopen the gripper, move clear of the board, align the fingers around the visible rod, and verify acquisition before lifting and attempting insertion; no human intervention is visibly required.
- Severity: low
- Severity evidence: The attempt fails to acquire the rod, but neither view shows displaced objects, damage, or other harmful consequences.
- Resetability: immediate
- Resetability evidence: The rod and board remain in their original usable state, so another aligned acquisition attempt requires no environmental reset.