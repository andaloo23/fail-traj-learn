# Episode: C0964

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: The tan toy is released onto the plate edge at frames 110–119, and the blue toy is placed on the plate at frames 353–363 (wrist_cam and overhead_cam). However, the pink-toy acquisition fails: frames 170–175 in wrist_cam show the closed gripper withdrawing while the pink toy remains on the table. Frames 386–391 in wrist_cam confirm that the pink toy is still off the plate. Thus, the task is visibly incomplete, not merely unconfirmed; no unwanted collision is clearly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 170 | No |
| 170 | 225 | Yes |
| 225 | 392 | No |

## Failure annotations

### Failure 1

- Frames: 170-225
- Categories: grasp
- Explanation: After closing near the pink toy at frames 163–169, the robot withdraws empty while the toy stays on the tabletop, visibly separated from the fingers at frames 170–175 in wrist_cam. It then carries the empty gripper toward the plate and opens it at frames 217–224 (wrist_cam and overhead_cam), completing an unsuccessful pick-and-place motion without advancing the pink toy.
- Recovery: Return to the pink toy with clearance from the plate and other toys, realign the fingers around its body, and verify possession with a short lift before transporting it to an open area of the plate; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The pink toy remains on the table, with no visible damage or meaningful damage risk; the consequence is a missed placement and wasted motion.
- Resetability: immediate
- Resetability evidence: The toy remains accessible on the tabletop and the environment requires no visible resetting before another grasp attempt.