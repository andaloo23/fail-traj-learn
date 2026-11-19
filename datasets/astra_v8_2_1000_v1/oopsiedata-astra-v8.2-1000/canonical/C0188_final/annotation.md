# Episode: C0188

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: The pink toy is on the plate by frame 45 and the tan toy by frame 270 in overhead_cam and wrist_cam. Repeated failed acquisitions leave the blue toy on the table, including at frames 945, 1380, 1650 and 1799. The final closed gripper withdraws without it at frames 1780–1799, establishing a visibly failed attempt rather than merely unconfirmed completion. No unwanted collision or damage is clearly established, and the recording ending does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 86 | No |
| 86 | 151 | Yes |
| 151 | 327 | No |
| 327 | 444 | Yes |
| 444 | 513 | No |
| 513 | 595 | Yes |
| 595 | 663 | No |
| 663 | 749 | Yes |
| 749 | 817 | No |
| 817 | 866 | Yes |
| 866 | 935 | No |
| 935 | 1001 | Yes |
| 1001 | 1087 | No |
| 1087 | 1092 | Yes |
| 1092 | 1109 | No |
| 1109 | 1153 | Yes |
| 1153 | 1223 | No |
| 1223 | 1271 | Yes |
| 1271 | 1357 | No |
| 1357 | 1424 | Yes |
| 1424 | 1515 | No |
| 1515 | 1559 | Yes |
| 1559 | 1630 | No |
| 1630 | 1693 | Yes |
| 1693 | 1780 | No |
| 1780 | 1800 | Yes |

## Failure annotations

### Failure 1

- Frames: 86-151
- Categories: grasp
- Explanation: At frames 86–90 in wrist_cam, the fingers close short of the tan toy. By frames 105–135, the gripper moves and holds empty near the plate while overhead_cam confirms the tan toy remains on the table. Reopening at frame 151 begins recovery.
- Recovery: Reopen, align around the tan toy’s body, and verify acquisition with a small lift before transferring; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition causes no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible and no environmental restoration is required.

### Failure 2

- Frames: 327-444
- Categories: grasp
- Explanation: wrist_cam shows an unsuccessful closure at frames 327–330, followed by empty departure at frame 345. overhead_cam shows the blue toy remaining on the tabletop throughout the subsequent empty positioning near the plate at frames 350–443. Reopening starts at frame 444.
- Recovery: Return with open fingers, correct the blue-toy grasp alignment, and verify a successful lift before transfer; no human intervention is needed.
- Severity: low
- Severity evidence: The toy remains unplaced without visible damage or harmful collision.
- Resetability: immediate
- Resetability evidence: The blue toy is accessible on the table and can be approached again without a reset.

### Failure 3

- Frames: 513-595
- Categories: grasp
- Explanation: At frame 513, wrist_cam shows the fingers closed without securing the blue toy. At frames 525–585, the gripper travels empty toward the plate while overhead_cam confirms the toy remains on the table. Reopening begins at frame 595.
- Recovery: Reopen and revise grasp position and height to enclose the toy, then verify retention before transferring; no human intervention is needed.
- Severity: low
- Severity evidence: The failed acquisition prevents placement but causes no visible damage or disruptive displacement.
- Resetability: immediate
- Resetability evidence: No scene restoration is needed before another attempt.

### Failure 4

- Frames: 663-749
- Categories: grasp
- Explanation: wrist_cam shows completed closure without acquisition at frame 663 and empty departure at frame 675. Empty positioning continues across frames 698–701 and toward the plate through frame 748, while overhead_cam shows the blue toy still on the table. Reopening at frame 749 ends this continuous failed attempt.
- Recovery: Return to the blue toy, adjust alignment using both views, and confirm that it lifts before moving toward the plate; no human intervention is needed.
- Severity: low
- Severity evidence: No damage or meaningful damage risk is visible; the blue toy simply remains unplaced.
- Resetability: immediate
- Resetability evidence: The workspace remains usable and the toy needs no retrieval or restoration.

### Failure 5

- Frames: 817-866
- Categories: grasp
- Explanation: At frame 817 in wrist_cam, the fingers finish closing without securing the blue toy. Frames 825–855 show empty movement toward the plate, with the toy remaining on the table in overhead_cam. Reopening begins at frame 866.
- Recovery: Reapproach with corrected finger placement and grasp height, and verify possession before transfer; no human intervention is needed.
- Severity: low
- Severity evidence: The missed grasp has no visible damaging consequence or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: Another attempt can begin without changing the environment.

### Failure 6

- Frames: 935-1001
- Categories: grasp
- Explanation: wrist_cam shows the blue toy unsecured outside the closed fingers at frame 935 and clearly left behind during departure at frame 945. overhead_cam confirms it remains on the tabletop, slightly reoriented, while the gripper continues empty toward the plate through frame 1000. Reopening starts at frame 1001.
- Recovery: Re-localize the toy in its current pose, grasp around its body, and verify retention before transferring; no human intervention is needed.
- Severity: low
- Severity evidence: The small pose change leaves the toy usable, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy can be grasped in its current accessible position without human restoration.

### Failure 7

- Frames: 1087-1092
- Categories: grasp
- Explanation: At frames 1087–1091, wrist_cam shows a completed empty closure while overhead_cam shows the blue toy on the table below the gripper. Reopening at frames 1092–1095 exposes the unsecured toy and begins a renewed acquisition attempt.
- Recovery: Adjust finger position and height after reopening so the next closure encloses the toy’s body; no human intervention is needed.
- Severity: low
- Severity evidence: This brief missed acquisition causes no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible and no environmental reset is required.

### Failure 8

- Frames: 1109-1153
- Categories: grasp
- Explanation: At frame 1109, wrist_cam shows the closed gripper with the blue toy outside it. Frames 1125–1140 show empty movement toward the plate while overhead_cam confirms the toy remains on the table. Reopening begins at frame 1153.
- Recovery: Return, correct the grasp alignment, and verify possession with a small lift before transfer; no human intervention is needed.
- Severity: low
- Severity evidence: The attempt leaves the toy unplaced without visible damage or disruptive collision.
- Resetability: immediate
- Resetability evidence: The existing scene permits another attempt without restoration.

### Failure 9

- Frames: 1223-1271
- Categories: grasp
- Explanation: wrist_cam shows completed closure without securing the blue toy at frame 1223, followed by empty departure at frames 1230–1245. overhead_cam confirms the toy remains on the table while empty positioning continues through frame 1270. Reopening begins at frame 1271.
- Recovery: Reapproach with open fingers surrounding a graspable part of the toy and confirm retention before leaving the pickup location; no human intervention is needed.
- Severity: low
- Severity evidence: Only acquisition and placement are prevented; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The tabletop and toy remain usable and accessible without intervention.

### Failure 10

- Frames: 1357-1424
- Categories: grasp
- Explanation: At frame 1357, wrist_cam shows a closed gripper without the blue toy. Frames 1365–1380 show the toy left behind during departure, and frames 1398–1423 show continued empty positioning near the plate. overhead_cam confirms the blue toy remains on the table. Reopening starts at frame 1424.
- Recovery: Stop the empty transfer, return with corrected alignment, and verify a successful lift before proceeding along a clear path to the plate; no human intervention is needed.
- Severity: low
- Severity evidence: No visible damage or harmful side effect accompanies this failed acquisition.
- Resetability: immediate
- Resetability evidence: The toy remains available for another attempt and no scene restoration is needed.

### Failure 11

- Frames: 1515-1559
- Categories: grasp
- Explanation: At frame 1515, wrist_cam shows the fingers closed without securing the blue toy. At frames 1530–1558, the gripper moves empty toward the plate while overhead_cam shows the toy remaining on the tabletop. Reopening begins at frame 1559.
- Recovery: Return with open fingers, revise grasp position and height, and confirm retention before transfer; no human intervention is needed.
- Severity: low
- Severity evidence: The failed attempt causes no visible damage, dropping, or disruptive collision.
- Resetability: immediate
- Resetability evidence: The toy and plate remain accessible and usable without a reset.

### Failure 12

- Frames: 1630-1693
- Categories: grasp
- Explanation: wrist_cam shows another completed empty closure at frame 1630 and separation from the blue toy during departure at frames 1635–1650. Empty positioning continues toward the plate through frame 1692, while overhead_cam confirms the toy remains on the table. Reopening starts at frame 1693.
- Recovery: Reapproach with revised alignment, close around the toy’s body, and verify a successful lift before moving toward the plate; no human intervention is needed.
- Severity: low
- Severity evidence: The toy remains unplaced, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: No object requires retrieval or restoration before another attempt.

### Failure 13

- Frames: 1780-1800
- Categories: grasp
- Explanation: At frame 1780, wrist_cam shows the fingers closed without securing the blue toy. By frames 1798–1799, the gripper withdraws empty and the toy is visibly separate; overhead_cam confirms it remains on the table. No recovery is visible before the episode ends.
- Recovery: Reopen, realign around the toy at an appropriate height, and verify retention with a small lift before transferring along a clear path; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The failed acquisition leaves the toy unplaced without visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible on the tabletop, so another attempt requires no environmental restoration.