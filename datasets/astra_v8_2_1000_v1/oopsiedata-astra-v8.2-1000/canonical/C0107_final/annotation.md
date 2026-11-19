# Episode: C0107

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: success but suboptimal
- Outcome evidence: The blue toy is released onto the plate at frames 176–188 (overhead_cam, wrist_cam). The first acquisition of the tan toy fails, with the gripper withdrawing empty at frames 295–311; a retry places it on the plate by frames 490–534. The pink toy is subsequently placed and released at frames 700–737. Frames 744–746 (wrist_cam) and 780–892 (overhead_cam) show all three toys remaining on the plate with the gripper withdrawn. No unwanted collision is clearly established; the failed tan-toy grasp makes completion suboptimal.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 283 | No |
| 283 | 313 | Yes |
| 313 | 893 | No |

## Failure annotations

### Failure 1

- Frames: 283-313
- Categories: grasp
- Explanation: At frames 283–294, the fingers finish closing without securing the tan toy (wrist_cam, overhead_cam). During frames 295–311, the closed gripper lifts away empty while the toy remains on the tabletop, confirming failed acquisition rather than an unfinished grasp. Reopening for a retry begins at frame 313.
- Recovery: Reopen the fingers, realign around the tan toy's body, descend with tabletop clearance, and verify retention with a small lift before transporting it to the plate; no human intervention is needed.
- Severity: low
- Severity evidence: The toy remains on the table, and neither camera shows damage or a meaningful damage risk from the missed acquisition.
- Resetability: immediate
- Resetability evidence: The tan toy remains accessible on the tabletop, so another grasp can be attempted without environmental resetting or human intervention.