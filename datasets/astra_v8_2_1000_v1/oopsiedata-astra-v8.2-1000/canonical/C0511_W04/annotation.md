# Episode: C0511_W04

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: Provisional for this window: overhead_cam and wrist_cam show the carrot remaining outside both bowls at frames 1050 and 1399. After prolonged inactivity, the gripper closes near it and withdraws without acquiring it (frames 1230–1262); subsequent open-gripper repositioning does not visibly complete sorting. Completion is unconfirmed, with a visibly unsuccessful acquisition in this window. Earlier context is limited to frames 1048–1049, and later execution is absent.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1230 | Yes |
| 1230 | 1243 | No |
| 1243 | 1263 | Yes |
| 1263 | 1400 | No |

## Failure annotations

### Failure 1

- Frames: 1050-1230
- Categories: task_not_attempted
- Explanation: overhead_cam and wrist_cam show the robot staying essentially in place beside the carrot throughout frames 1050–1229, with occasional small finger motions but no sustained acquisition or sorting progress over approximately 12 seconds. Frames 1048–1049 show the same pose, supporting continuity across the window boundary, although the earlier onset is not independently visible. More substantial closing/alignment begins at frame 1230.
- Recovery: Resume deliberate alignment around the carrot, acquire it, verify retention, and transfer it to the food bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is lost progress, without damage or a supported meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The carrot and bowls remain accessible on the tabletop; no environmental resetting is required.

### Failure 2

- Frames: 1243-1263
- Categories: grasp
- Explanation: In wrist_cam, the fingers finish closing by frame 1243 without securing the carrot, then the robot withdraws through frames 1250–1262. overhead_cam shows the orange carrot remaining on the tabletop rather than traveling with the gripper; its continued presence is clearer after the fingers reopen at frames 1263–1277. This establishes failed acquisition, not a confirmed drop or hardware malfunction.
- Recovery: Open the fingers, realign them around the carrot’s body rather than beside it, and verify a secure grasp before lifting toward the food bowl; no human intervention is evidently required.
- Severity: low
- Severity evidence: The carrot remains on the usable tabletop with no visible damage; the attempt merely fails to acquire it.
- Resetability: immediate
- Resetability evidence: The target remains within reach, permitting another attempt without human or environmental reset.