# Episode: C0360

## Episode annotation

- Language task: Pick up the green cup and stack it on the purple cup.
- Success label: failure
- Outcome evidence: The cups begin separately on the table (frame 0, camera_high). The robot repeatedly approaches the green cup but withdraws without it; both cups remain separately on the table at frames 301, 557 and 599 in camera_high, corroborated by camera_wrist_right. No stack is formed; this is visibly unsuccessful acquisition, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 140 | No |
| 140 | 155 | Yes |
| 155 | 272 | No |
| 272 | 350 | Yes |
| 350 | 506 | No |
| 506 | 600 | Yes |

## Failure annotations

### Failure 1

- Frames: 140-155
- Categories: grasp
- Explanation: After closing near the green cup, the gripper rises without acquiring it (frames 140-154, camera_wrist_right and camera_high). By frame 151 the green cup remains on the table beneath the withdrawing gripper. The robot begins another approach at frame 155.
- Recovery: Reopen and realign the fingers around the green cup, then close and verify that the cup follows a small test lift; no human intervention is needed.
- Severity: low
- Severity evidence: The cup stays on the table, with no visible damage, spill or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: Both cups remain upright and accessible; another acquisition can be attempted without environmental intervention.

### Failure 2

- Frames: 272-350
- Categories: grasp
- Explanation: Following another closure near the green cup, the robot withdraws empty and moves toward the purple cup (frames 272-301, camera_high and camera_wrist_right). The green cup remains on the table while the empty gripper continues the motion over the purple cup through frame 349; this cannot advance stacking.
- Recovery: Return to the green cup with open fingers, correct the grasp alignment and confirm possession before transporting toward the purple cup; no human intervention is needed.
- Severity: low
- Severity evidence: The attempt fails to lift the green cup; both cups remain on the usable tabletop without visible damage.
- Resetability: immediate
- Resetability evidence: The green cup is slightly displaced but remains upright and reachable, requiring no external reset.

### Failure 3

- Frames: 506-600
- Categories: grasp
- Explanation: After returning to and closing near the green cup, the gripper again withdraws without it (frames 506-527, camera_high and camera_wrist_right). Subsequent movement near and away from the purple cup is empty-handed; frames 557-599 show both cups still separate on the table. No successful acquisition or stacking follows.
- Recovery: Reapproach the green cup, establish a secure grasp and verify a short lift before attempting placement; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is another unsuccessful pickup and incomplete stack, with no visible damage or spill.
- Resetability: immediate
- Resetability evidence: Both cups remain upright on the table and available for another attempt without human resetting.
