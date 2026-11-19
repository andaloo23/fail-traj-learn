# Episode: C0882

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Only the blue toy is placed on the plate, with release visible at frames 525–530 in wrist_cam and overhead_cam. At frame 607, both cameras show the pink and tan toys still on the table beside the plate, so the full task is visibly incomplete. Earlier empty-handed withdrawals establish failed acquisition attempts; no unwanted collision or damage is clearly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 76 | No |
| 76 | 127 | Yes |
| 127 | 203 | No |
| 203 | 326 | Yes |
| 326 | 608 | No |

## Failure annotations

### Failure 1

- Frames: 76-127
- Categories: grasp
- Explanation: After closing beside the blue toy at frames 65–75, the robot withdraws and moves toward the plate without acquiring it. In overhead_cam the toys remain on the table, while wrist_cam shows the closed, empty gripper during frames 76–126; the plate remains empty. Opening the gripper at frame 127 begins preparation for another attempt.
- Recovery: Reopen the gripper, align its fingers on opposite sides of the toy, and verify acquisition with a short lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The attempt produces no placement, but no damage or meaningful damage risk is visible in either camera.
- Resetability: immediate
- Resetability evidence: The toys and plate remain available on the tabletop, so another acquisition attempt requires no environmental reset.

### Failure 2

- Frames: 203-326
- Categories: grasp
- Explanation: The gripper closes near the pink toy at frames 192–201 but then moves away empty from frame 203 onward. wrist_cam shows the pink toy remaining on the tabletop at frames 213–240 and all three toys still outside the empty plate at frames 295–305; overhead_cam corroborates the unsuccessful withdrawal. The subsequent empty-handed movement toward the plate does not transport a toy, and reopening begins at frame 326.
- Recovery: Return with the gripper open, correct the alignment around the pink toy, and confirm a secure lift before moving to the plate; no human intervention is needed.
- Severity: low
- Severity evidence: No toy is transferred during this attempt, and neither camera establishes damage or a harmful collision.
- Resetability: immediate
- Resetability evidence: The missed toy remains accessible on the table and the environment needs no manual restoration before retrying.