# Episode: C0176

## Episode annotation

- Language task: Pick green block and place on cardboard.
- Success label: failure
- Outcome evidence: In exterior_cam, the green block starts beside the cardboard at frame 0, is visibly carried in the gripper at frames 250–300, and falls onto the tabletop away from the cardboard at frames 301–307. The robot subsequently approaches the fallen block but never visibly transfers it to the cardboard; the cardboard remains empty at frame 599. This is a visibly failed transfer, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 301 | No |
| 301 | 308 | Yes |
| 308 | 483 | No |
| 483 | 600 | Yes |

## Failure annotations

### Failure 1

- Frames: 301-308
- Categories: grasp
- Explanation: In exterior_cam, the block separates from the gripper at frame 301, falls at frames 302–304, and settles on the foreground tabletop by frame 307, well away from the cardboard. Retention fails during transport; the images do not establish why the gripper releases it.
- Recovery: Locate the fallen block, align the fingers around it, reacquire it, and verify retention with a short lift before transporting it over the cardboard; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The block falls onto the otherwise clear tabletop, with no visible damage or disruption to unrelated objects.
- Resetability: immediate
- Resetability evidence: The block remains on the tabletop and available for another acquisition attempt; no environmental repair or human reset is visibly required.

### Failure 2

- Frames: 483-600
- Categories: task_not_attempted
- Explanation: After approaching the fallen block, the robot remains in essentially the same low foreground pose through frames 483–599 in exterior_cam. Minor gripper or arm adjustments produce no visible acquisition, lift, or progress toward the empty cardboard, establishing sustained unproductive behavior rather than a brief pause.
- Recovery: Reassess the block and finger positions, withdraw enough to obtain a clear alignment, and execute a verified grasp before resuming placement; human intervention is not visibly required.
- Severity: low
- Severity evidence: The observed consequence is stalled task progress; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The block and cardboard remain available on the table, so another attempt does not visibly require environmental resetting.