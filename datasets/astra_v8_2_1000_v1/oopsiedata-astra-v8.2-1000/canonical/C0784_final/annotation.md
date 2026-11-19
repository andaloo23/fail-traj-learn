# Episode: C0784

## Episode annotation

- Language task: pick up the blue peg and insert it into the green peghole
- Success label: failure
- Outcome evidence: The robot lifts the blue peg twice (side and wrist, frames 24–80 and 114–160), but drops it onto the table away from the green peghole (side, frames 82–86 and 161–164). Subsequent positioning does not produce insertion; the peg remains separate from the visibly empty green hole through frame 268 (front and side). This is an observed unsuccessful episode with visible drops, not merely an occluded or unconfirmed insertion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 81 | No |
| 81 | 85 | Yes |
| 85 | 161 | No |
| 161 | 164 | Yes |
| 164 | 180 | No |
| 180 | 269 | Yes |

## Failure annotations

### Failure 1

- Frames: 81-85
- Categories: grasp
- Explanation: After carrying the blue peg, the fingers open at frame 81 (wrist), and the peg separates and falls onto the tabletop at frames 82–84 (side). It is released away from the green hole rather than inserted, undoing the successful pickup. At frame 85 the arm starts approaching the fallen peg again.
- Recovery: Reacquire the peg with a secure grasp, verify retention with a small lift, and align it above the green hole before lowering and releasing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The peg falls onto the clear tabletop; no damage or disruption to other objects is visible.
- Resetability: immediate
- Resetability evidence: The peg remains accessible on the table and the green holder stays upright, allowing another attempt without human resetting.

### Failure 2

- Frames: 161-164
- Categories: grasp
- Explanation: Following the second pickup, the peg leaves the fingers at frame 161 and falls onto the table at frames 162–163 (side and wrist), again outside the green hole. Recovery movement toward the peg begins at frame 164.
- Recovery: Regrasp the peg, verify secure retention, and maintain the grasp during transport and alignment; release only after the peg is supported inside the hole. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The second drop leaves the peg on the tabletop with no visible damage to it, the holder, or the robot.
- Resetability: immediate
- Resetability evidence: Both task objects remain accessible and usable in their visible state; another acquisition can be attempted directly.

### Failure 3

- Frames: 180-269
- Categories: task_not_attempted
- Explanation: After returning toward the fallen peg, the robot remains beside it with open fingers and only small positional changes for the remainder of the episode (side and wrist, frames 180, 200, 230, and 268). No renewed acquisition or movement toward insertion is established, constituting sustained unproductive behavior rather than a brief pause.
- Recovery: Reposition the open fingers to straddle the peg, close securely, verify pickup, and then transport and align it with the green hole; no environmental human intervention is visibly required.
- Severity: low
- Severity evidence: The sustained lack of progress prevents completion but causes no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The peg remains on the reachable tabletop and the holder remains upright and empty; no environmental reset is needed to resume a task-directed attempt.