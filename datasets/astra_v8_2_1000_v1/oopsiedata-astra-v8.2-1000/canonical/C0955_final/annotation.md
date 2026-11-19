# Episode: C0955

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: The robot makes unsuccessful acquisitions of the beige and blue toys, then successfully places the pink toy on the plate at frames 621–625 (overhead_cam and wrist_cam). At frames 710–713, both cameras show the pink toy on the plate while the blue and beige toys remain on the table. Thus only part of the task is completed, with visibly failed attempts rather than merely unconfirmed completion. No unwanted collision or damage is clearly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 83 | No |
| 83 | 175 | Yes |
| 175 | 303 | No |
| 303 | 397 | Yes |
| 397 | 714 | No |

## Failure annotations

### Failure 1

- Frames: 83-175
- Categories: grasp
- Explanation: After closing near the beige toy at frames 74–82, the robot withdraws and moves away empty starting at frame 83 (overhead_cam and wrist_cam). The beige toy remains on the table, clearly visible again at frames 144–160 in wrist_cam, while the plate remains empty in overhead_cam. The closed, empty withdrawal does not transfer the target; opening for another attempt begins at frame 175.
- Recovery: Reopen the gripper, realign its fingers around the beige toy's body, and verify a secure acquisition with a short lift before transporting it to the plate; no human intervention is needed.
- Severity: low
- Severity evidence: The toy remains on the tabletop, with no visible damage or meaningful damage risk from the missed acquisition.
- Resetability: immediate
- Resetability evidence: The toy and plate remain accessible and usable; another acquisition can be attempted without environmental resetting.

### Failure 2

- Frames: 303-397
- Categories: grasp
- Explanation: The gripper closes near the blue toy at frames 293–302, then moves away empty from frame 303 onward (wrist_cam and overhead_cam). Frames 307–320 in overhead_cam show the blue toy still beside the empty plate as the arm withdraws; wrist_cam confirms it remains on the table at frames 382–396. The robot begins reopening at frame 397.
- Recovery: Reopen and align around the blue toy's body rather than closing beside it, verify retention with a short lift, and then carry it above the plate with clearance; no human intervention is needed.
- Severity: low
- Severity evidence: The failed acquisition leaves the blue toy on the table without visible damage or disruption to the scene.
- Resetability: immediate
- Resetability evidence: No cleanup, retrieval, or manual repositioning is required before retrying the accessible toy.