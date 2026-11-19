# Episode: C0298

## Episode annotation

- Language task: Pick green block and place on cardboard.
- Success label: failure
- Outcome evidence: In exterior_cam, the green block remains on the tabletop to the right of the cardboard at frames 0, 150, 300, 450 and 599. The empty gripper repeatedly moves above and to the left of the cardboard without acquiring the block. The task is visibly unachieved throughout the observed episode, with sustained unproductive movement rather than an unfinished near-object grasp; no abnormal termination is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 30 | No |
| 30 | 600 | Yes |

## Failure annotations

### Failure 1

- Frames: 30-600
- Categories: task_not_attempted
- Explanation: After initial positioning, the gripper moves leftward away from the green block beginning at frame 30 in exterior_cam, then repeatedly changes position and orientation over empty space near the left side of the table and cardboard (frames 65, 105, 217, 321, 401 and 473). This sustained activity never develops into an approach to or acquisition of the block, which remains unchanged through frame 599. No contact, failed retention or hidden mechanical cause is established.
- Recovery: Locate the green block again, plan a clear approach above it, align and lower the open gripper, then grasp and verify possession before transferring it onto the cardboard; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task makes no progress, but exterior_cam shows no displaced objects, damage or established harmful collision through frame 599.
- Resetability: immediate
- Resetability evidence: The block and cardboard remain in their original usable positions, so another task-directed attempt requires no environmental reset or human intervention.