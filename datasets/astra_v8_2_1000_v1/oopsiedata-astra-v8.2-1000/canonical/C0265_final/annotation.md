# Episode: C0265

## Episode annotation

- Language task: find the cube under the green bowl
- Success label: failure
- Outcome evidence: The robot repeatedly repositions near the green bowl, but no cube is visibly uncovered. The bowl remains inverted on the table in left and top at frames 0, 690, 1140, 1500 and 1999; right also provides no evidence of finding the cube. Completion is unconfirmed, rather than a clearly demonstrated failed grasp: acquisition and subsequent loss of possession are not established. A sustained unproductive interval is visible before repositioning resumes at frame 1845. The recording ends without a visible lift or inspection beneath the bowl, but does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1380 | No |
| 1380 | 1845 | Yes |
| 1845 | 2000 | No |

## Failure annotations

### Failure 1

- Frames: 1380-1845
- Categories: task_not_attempted
- Explanation: After earlier approach and viewpoint adjustments, the robot remains apart from the bowl with only gradual positional drift and no discernible uncovering attempt for approximately 15.5 seconds (left, right and top, frames 1380, 1500, 1650, 1750 and 1844). This sustained unproductive behavior leaves the bowl unchanged and does not advance finding the cube. Frame 1380 is an approximate onset supported by the selected checks following repositioning around frame 1350; the exact transition from preparation to stalling is uncertain. The same interval continues across frame 1750 without a distinct new failure. Renewed repositioning begins at frame 1845 and brings the left gripper nearer the bowl by frame 1860.
- Recovery: Resume a deliberate approach, align for a secure grasp of the bowl, lift it clear, and inspect beneath it for the cube; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is delayed task progress; no damage, displaced unrelated objects, or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The bowl and surrounding environment remain usable and need no resetting; the robot can resume a task-directed attempt without human intervention.