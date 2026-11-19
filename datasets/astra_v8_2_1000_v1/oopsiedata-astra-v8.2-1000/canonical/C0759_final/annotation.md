# Episode: C0759

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: The pink and tan toys reach the plate (wrist_cam, frames 165 and 870), and the blue toy is finally placed there by frame 1545. However, subsequent low gripper movement displaces the plate and leaves the tan toy outside it (overhead_cam and wrist_cam, frames 1559–1588). At frame 1799, overhead_cam shows the pink and blue toys on the plate and the tan toy beside it. Thus the final arrangement visibly fails the task, rather than merely lacking confirmation; unwanted collisions and repeated failed attempts also occur. Selected visual checks limit exact boundary precision, particularly around the recovery near frame 360.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 46 | No |
| 46 | 50 | Yes |
| 50 | 260 | No |
| 260 | 278 | Yes |
| 278 | 324 | No |
| 324 | 360 | Yes |
| 360 | 502 | No |
| 502 | 532 | Yes |
| 532 | 571 | No |
| 571 | 636 | Yes |
| 636 | 976 | No |
| 976 | 997 | Yes |
| 997 | 1173 | No |
| 1173 | 1185 | Yes |
| 1185 | 1223 | No |
| 1223 | 1333 | Yes |
| 1333 | 1559 | No |
| 1559 | 1589 | Yes |
| 1589 | 1800 | No |

## Failure annotations

### Failure 1

- Frames: 46-50
- Categories: collision
- Explanation: During the pink-toy approach, the neighboring tan toy abruptly tips and shifts away at frames 46–49 in wrist_cam; overhead_cam shows the gripper descending among the toys. This unintended displacement violates the no-collisions requirement.
- Recovery: Establish clearance from the displaced tan toy and realign around the pink toy before continuing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The soft toy is displaced on the tabletop without visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible in its new pose without human resetting.

### Failure 2

- Frames: 260-278
- Categories: manipulation
- Explanation: After carrying the tan toy toward the plate, the robot opens its fingers at frames 260–261 and leaves it outside the rim, clearly visible at frames 270–277 in wrist_cam and overhead_cam. Established possession ends in an unsuccessful placement.
- Recovery: Reacquire the tan toy, lift clear of the rim and pink toy, and release fully over the plate; no human intervention appears necessary.
- Severity: low
- Severity evidence: The toy lands on the tabletop with no visible damage.
- Resetability: immediate
- Resetability evidence: The misplaced toy remains accessible for another attempt without environmental intervention.

### Failure 3

- Frames: 324-360
- Categories: grasp
- Explanation: After closing near the blue toy, the gripper withdraws empty at frames 324–330 and travels toward the plate while the blue toy remains on the table (overhead_cam, wrist_cam). The empty transfer persists through frames 345–351; renewed approach is evident by frame 360. The recovery boundary is approximate because the selected checks do not establish its exact onset between frames 351 and 360.
- Recovery: Return with open fingers, align around the blue toy’s body, and verify retention with a small lift before transport; no human intervention appears necessary.
- Severity: low
- Severity evidence: The missed acquisition leaves the toy on the tabletop without visible damage.
- Resetability: immediate
- Resetability evidence: The blue toy is available for an immediate retry without scene resetting.

### Failure 4

- Frames: 502-532
- Categories: manipulation
- Explanation: After visibly transporting the blue toy at frames 420–495, the robot opens its fingers outside the plate at frames 502–510. The toy remains on the table during withdrawal at frames 525–531 (overhead_cam, wrist_cam), so the established grasp does not result in placement on the plate.
- Recovery: Reacquire the blue toy and position it fully above an unoccupied area of the plate before lowering and releasing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The soft toy lands on the table with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible beside the plate without requiring an environmental reset.

### Failure 5

- Frames: 571-636
- Categories: grasp
- Explanation: Following closure near the blue toy, the gripper withdraws empty from frame 571 onward while the toy stays on the tabletop, clearly separated by frames 585–600. The robot continues toward the plate and opens empty by frame 630 (overhead_cam, wrist_cam), completing an unproductive transfer.
- Recovery: Realign open fingers around the blue toy and verify a retained grasp before attempting another transfer; no human intervention appears necessary.
- Severity: low
- Severity evidence: The failed acquisition delays placement but causes no visible damage.
- Resetability: immediate
- Resetability evidence: The target remains accessible in the existing scene for another attempt.

### Failure 6

- Frames: 976-997
- Categories: grasp
- Explanation: After finger closure at frames 974–975, the gripper lifts away without the blue toy starting at frame 976; frames 990–996 clearly show the toy remaining on the tabletop (overhead_cam, wrist_cam). Opening for another approach begins at frame 997.
- Recovery: Open and realign around the blue toy’s body, then verify retention with a small lift before transport; no human intervention appears necessary.
- Severity: low
- Severity evidence: The toy remains on the table without visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: No scene intervention is needed to retry acquisition.

### Failure 7

- Frames: 1173-1185
- Categories: manipulation
- Explanation: After carrying the blue toy toward the plate at frames 1095–1172, the robot opens its fingers at frames 1173–1174 and releases outside the rim. The toy lies on the tabletop beside the plate at frames 1183–1184 (overhead_cam, wrist_cam), establishing an unsuccessful placement.
- Recovery: Reacquire the toy, position it fully inside the plate’s footprint with rim clearance, and lower before releasing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The toy falls onto the tabletop without visible damage.
- Resetability: immediate
- Resetability evidence: The misplaced toy remains within the accessible workspace for another attempt.

### Failure 8

- Frames: 1223-1333
- Categories: task_not_attempted
- Explanation: Following an approach toward the blue toy, the empty, open gripper retreats over bare tabletop at frames 1223–1260 and remains away with little change through frame 1332 (overhead_cam, wrist_cam). This sustained unproductive interval leaves the toy beside the plate; renewed task-directed approach follows.
- Recovery: Resume a clearance-preserving approach to the blue toy and verify acquisition before transporting it onto the plate; no human intervention is visibly required.
- Severity: low
- Severity evidence: The interval delays completion without visible damage or unwanted object displacement.
- Resetability: immediate
- Resetability evidence: The toy and plate remain available in their existing positions, requiring no environmental reset.

### Failure 9

- Frames: 1559-1589
- Categories: collision
- Explanation: After placing the blue toy, the open gripper continues moving low among the toys and plate. The blue toy shifts abruptly at frames 1559–1560 in wrist_cam, and the plate slides across the tabletop through frames 1575–1588 in overhead_cam. The tan toy becomes separated from the plate, disrupting the achieved arrangement and violating the no-collisions requirement.
- Recovery: Lift vertically clear of the arrangement, reassess object positions, and reacquire the tan toy for placement fully inside the rim; withdraw with adequate clearance. No human intervention appears necessary.
- Severity: low
- Severity evidence: The plate and toys are displaced but remain on the tabletop; no breakage or meaningful damage risk is visibly established.
- Resetability: immediate
- Resetability evidence: The plate and displaced tan toy remain accessible, allowing another attempt from their current positions without human resetting.