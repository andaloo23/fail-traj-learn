# Episode: C0889_W01

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisionally, the task is not completed in this window: the plate remains empty, and the beige toy remains beside it at frames 150, 230 and 349 in overhead_cam and wrist_cam. The robot moves the beige toy toward the plate but releases it outside the rim, then makes an unsuccessful acquisition attempt. The other toys remain on the table. Later episode context is absent; this is not evidence of episode termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 137 | No |
| 137 | 144 | Yes |
| 144 | 180 | No |
| 180 | 216 | Yes |
| 216 | 350 | No |

## Failure annotations

### Failure 1

- Frames: 137-144
- Categories: manipulation
- Explanation: After moving the beige toy from its initial position toward the plate, the robot opens its gripper at frames 137-143 while the toy is outside the plate rim. overhead_cam shows the toy left on the tabletop beside the plate, and wrist_cam confirms this placement as the gripper moves away at frames 144-150. The transfer therefore does not accomplish placement on the plate; no damaging collision is established.
- Recovery: Reacquire the beige toy, lift it clear of the rim, move above the plate interior, and release only when its footprint is inside the plate; human intervention is not visibly needed.
- Severity: low
- Severity evidence: The toy remains on the table beside an intact plate, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible to the robot, so another attempt requires no environmental reset or human intervention.

### Failure 2

- Frames: 180-216
- Categories: grasp
- Explanation: Following the renewed approach and finger closure at frames 169-179, the gripper withdraws without the beige toy at frames 180-188 in overhead_cam; the toy remains on the tabletop. The robot then moves the closed, empty gripper toward the plate and opens it at frames 212-215, as seen in wrist_cam, without placing anything. This establishes failed acquisition rather than merely an unfinished closure.
- Recovery: Reopen and realign the fingers around the toy's body, keeping clearance from the plate, then verify that the toy lifts with the gripper before attempting another transfer; human intervention is not visibly needed.
- Severity: low
- Severity evidence: The failed acquisition leaves the toy on the tabletop, with no visible breakage, spill or other damaging consequence.
- Resetability: immediate
- Resetability evidence: The toy and plate remain accessible and usable; the robot can retry without a human resetting the scene.