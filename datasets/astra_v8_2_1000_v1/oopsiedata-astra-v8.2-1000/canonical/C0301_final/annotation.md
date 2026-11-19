# Episode: C0301

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: The robot makes partial progress: overhead_cam and wrist_cam show the pink toy lifted at frames 1680–1695 and deposited in the blue bowl by frame 1725. However, wrist_cam at frames 1750 and 1798–1799 shows the blue toy and food-shaped objects still on the tabletop, so sorting is visibly incomplete. Earlier empty withdrawals establish failed acquisitions, including frames 152–165 and 389–405 in both cameras. The final repositioning does not establish another failed acquisition or abnormal termination; completion beyond the recording is unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 152 | No |
| 152 | 211 | Yes |
| 211 | 389 | No |
| 389 | 412 | Yes |
| 412 | 839 | No |
| 839 | 857 | Yes |
| 857 | 1158 | No |
| 1158 | 1190 | Yes |
| 1190 | 1311 | No |
| 1311 | 1336 | Yes |
| 1336 | 1800 | No |

## Failure annotations

### Failure 1

- Frames: 152-211
- Categories: grasp
- Explanation: Following closure near the carrot-shaped item at frames 150–151 in wrist_cam, the gripper withdraws beginning at frame 152 without acquiring an object. At frame 165, overhead_cam and wrist_cam show the food items remaining on the table and the gripper empty. The subsequent empty transfer and opening near the bowls at frames 209–210 make no sorting progress; repositioning resumes at frame 211.
- Recovery: Recenter the open fingers around an isolated food item and verify retention during a short lift before transferring it to the food bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The items remain on the tabletop with no visible damage, spill, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The objects remain accessible and the bowls upright, allowing another attempt without environmental resetting.

### Failure 2

- Frames: 389-412
- Categories: grasp
- Explanation: After closure beside the pink toy at frames 387–388 in wrist_cam, the robot withdraws beginning at frame 389. By frames 405–411, overhead_cam shows the empty gripper separated from the toy, which remains on the table; wrist_cam corroborates the separation. Repositioning resumes at frame 412.
- Recovery: Align the fingers around a graspable portion of the pink toy at an appropriate height and confirm a secure lift before transfer; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The missed acquisition prevents sorting progress but causes no visible damage or harmful disturbance.
- Resetability: immediate
- Resetability evidence: The pink toy remains accessible on the tabletop and no scene reset is needed.

### Failure 3

- Frames: 839-857
- Categories: grasp
- Explanation: Acquisition motions beside the pink toy in wrist_cam at frames 735–780 are followed by withdrawal beginning at frame 839. At frames 855–856, overhead_cam shows the gripper raised empty while the pink toy remains on the tabletop, corroborated by wrist_cam. No secure possession or drop is established; reorientation resumes at frame 857.
- Recovery: Adjust the approach orientation and center the fingers around the toy, then verify that it moves with the gripper during a short lift before transporting it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy remains on the table without visible damage, and both bowls remain upright.
- Resetability: immediate
- Resetability evidence: Another aligned acquisition can be attempted without human intervention or environmental resetting.

### Failure 4

- Frames: 1158-1190
- Categories: grasp
- Explanation: Following acquisition motions near the object cluster at frames 1125–1140 in wrist_cam, the robot withdraws empty beginning at frame 1158. Frames 1170–1189 in overhead_cam show it moving away and lifting without an object, while wrist_cam shows the objects remaining on the table. The precise target is partly obscured; no specific target identity or hidden cause is established. Repositioning resumes at frame 1190.
- Recovery: Select a clearly identified object, align the fingers around it, and verify retention before transferring it to the appropriate bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: This attempt produces no visible placement, damage, spill, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The objects remain accessible and the scene requires no resetting before another attempt.

### Failure 5

- Frames: 1311-1336
- Categories: grasp
- Explanation: After closing near the pink toy at frames 1309–1310 in wrist_cam, the gripper moves away beginning at frame 1311 without retaining it. Frames 1320–1335 in overhead_cam show the raised empty gripper and the toy remaining on the table; wrist_cam corroborates their separation. Repositioning resumes at frame 1336.
- Recovery: Reapproach with the fingers centered around the toy's body and confirm retention during a short lift before transfer to the toy bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The missed acquisition leaves the toy on the tabletop with no visible damage or harmful disturbance.
- Resetability: immediate
- Resetability evidence: The toy remains accessible for another attempt without an environmental reset.