# Episode: C0889

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: The task remains incomplete: overhead_cam and wrist_cam at frames 750–765 show the beige toy placed at least partly on the plate rim, but frames 1471 and 1799 show the remaining toys still on the tabletop. Earlier unsuccessful placement and acquisitions are visible at frames 137–150, 180–215 and 367–405; the pink toy is also missed at frames 1144–1215. The proposed failed acquisition at frames 660–700 is not retained: the continued sequence through frames 735–765 shows the beige toy reaching the plate, rather than establishing an empty withdrawal. No unwanted collision or damage is clearly established. Completion is not merely hidden at the ending: toys visibly remain unplaced, although the recording end does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 137 | No |
| 137 | 144 | Yes |
| 144 | 180 | No |
| 180 | 216 | Yes |
| 216 | 367 | No |
| 367 | 406 | Yes |
| 406 | 530 | No |
| 530 | 649 | Yes |
| 649 | 934 | No |
| 934 | 1136 | Yes |
| 1136 | 1144 | No |
| 1144 | 1220 | Yes |
| 1220 | 1234 | No |
| 1234 | 1398 | Yes |
| 1398 | 1471 | No |
| 1471 | 1800 | Yes |

## Failure annotations

### Failure 1

- Frames: 137-144
- Categories: manipulation
- Explanation: After carrying the beige toy toward the plate, the robot opens its fingers outside the rim at frames 137–143. overhead_cam and wrist_cam at frames 144–150 show the toy left beside the plate rather than placed on it.
- Recovery: Reacquire the toy, lift clear of the rim, and release above the plate interior after checking its footprint; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy remains on the tabletop beside an intact plate, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible for another attempt without environmental resetting.

### Failure 2

- Frames: 180-216
- Categories: grasp
- Explanation: Following finger closure, the gripper withdraws empty while the beige toy remains on the table. overhead_cam and wrist_cam at frames 180, 195 and 210–215 show the unsuccessful withdrawal and subsequent opening without a transfer.
- Recovery: Open and align the fingers around the toy's body, then verify that it lifts with the gripper before transferring it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The missed acquisition prevents progress but causes no visible damage or damaging impact.
- Resetability: immediate
- Resetability evidence: The target remains accessible beside the plate, requiring no human reset.

### Failure 3

- Frames: 367-406
- Categories: grasp
- Explanation: After closure, the gripper shifts and rotates without acquiring the beige toy. wrist_cam at frames 367, 390 and 405 shows the toy remaining outside the fingers beside the plate, while overhead_cam confirms no transfer; reopening begins at frame 406.
- Recovery: Reopen and center the toy between the fingers with clearance from the rim, then verify possession with a short lift; no human intervention is visibly required.
- Severity: low
- Severity evidence: The toy remains on the table and no damage to the toy, plate or robot is visible.
- Resetability: immediate
- Resetability evidence: Another acquisition can be attempted without altering or repairing the environment.

### Failure 4

- Frames: 530-649
- Categories: task_not_attempted
- Explanation: overhead_cam and wrist_cam at frames 530, 570, 600 and 645 show the open gripper remaining beside the beige toy with only small adjustments and no discernible acquisition or transfer for approximately eight seconds. Renewed closure starts at frame 649.
- Recovery: Resume deliberate alignment and acquisition, verify a clear lift, and transfer above the plate while maintaining clearance; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The consequence is sustained delay, without observed damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The pause does not create a scene condition requiring environmental intervention.

### Failure 5

- Frames: 934-1136
- Categories: task_not_attempted
- Explanation: After approaching the remaining toys, the robot holds its open gripper beside the pink toy without acquiring it. overhead_cam and wrist_cam at frames 934, 990, 1050, 1110 and 1135 establish one continuous unproductive interval across the window boundary, ending when closure begins at frame 1136.
- Recovery: Center the pink toy's body between the fingers with clearance from neighboring toys, then grasp and verify possession before transfer; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Sustained lack of progress is visible, but no damage or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The toys remain accessible and the plate usable, so no environmental reset is needed.

### Failure 6

- Frames: 1144-1220
- Categories: grasp
- Explanation: wrist_cam at frames 1144–1145 shows the fingers closing beside rather than around the pink toy. The closed gripper subsequently moves toward the plate empty, while the toy remains on the tabletop, as shown in overhead_cam and wrist_cam at frames 1170, 1200 and 1215. Movement back toward the toys begins around frame 1220.
- Recovery: Return with clearance, reopen and align around the toy, and confirm possession with a short lift before beginning another transfer; no human intervention is visibly required.
- Severity: low
- Severity evidence: The failed acquisition causes no visible dropping, damage or clearly established unwanted collision.
- Resetability: immediate
- Resetability evidence: The missed toy remains on the accessible tabletop and requires no human resetting.

### Failure 7

- Frames: 1234-1398
- Categories: task_not_attempted
- Explanation: Following a brief return toward the toys, the robot repeatedly moves its closed, empty gripper near the plate without acquiring anything. overhead_cam and wrist_cam at frames 1234, 1275, 1320, 1365 and 1395 show sustained back-and-forth movement without task progress. Reopening at frame 1398 begins the subsequent recovery approach.
- Recovery: Stop the empty movements, open the gripper, align around an accessible toy and verify acquisition before transferring it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The observed consequence is wasted motion and delay, without visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The scene remains usable and does not require environmental resetting.

### Failure 8

- Frames: 1471-1800
- Categories: task_not_attempted
- Explanation: overhead_cam and wrist_cam at frames 1471, 1530, 1605, 1749 and 1799 show the open gripper beside the pink-and-white toy without acquisition or placement. Small initial adjustments give way to an essentially unchanged pose, establishing sustained unproductive behavior continuing through the ending rather than separate failures at window boundaries.
- Recovery: Reassess the toy position, align the fingers around its body with clearance from nearby objects, and verify a grasp and lift before transferring it; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is prolonged delay and an incomplete task; no damage or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The toys remain accessible on the tabletop and another attempt needs no environmental reset.