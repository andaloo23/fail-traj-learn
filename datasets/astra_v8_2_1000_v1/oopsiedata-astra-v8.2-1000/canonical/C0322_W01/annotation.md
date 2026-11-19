# Episode: C0322_W01

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: In overhead_cam and wrist_cam, the robot approaches and grasps the beige toy (frames 40–70), but releases it onto the table outside the plate (frames 155–167). It approaches the toy again and closes the gripper (frames 200–250), then opens beside the plate again at frames 345–349. The plate remains empty and the other toys remain on the table at frame 349. This is a provisional window outcome with a visibly unsuccessful placement; later completion is unknown because later context is not supplied. No unwanted collision is clearly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 155 | No |
| 155 | 168 | Yes |
| 168 | 345 | No |
| 345 | 350 | Yes |

## Failure annotations

### Failure 1

- Frames: 155-168
- Categories: manipulation
- Explanation: After carrying the beige toy toward the plate, the robot opens its gripper outside the rim at frames 155–160 in wrist_cam. The toy falls onto the tabletop and moves farther from the plate through frames 161–167, also visible in overhead_cam. This release does not place the toy on the plate.
- Recovery: Reacquire the beige toy, lift it clear of the table and plate rim, and position it fully above the plate before lowering and releasing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The small toy lands on the tabletop; no damage to the toy, plate, or robot is visible.
- Resetability: immediate
- Resetability evidence: The toy remains accessible on the table, allowing another acquisition attempt without environmental resetting.

### Failure 2

- Frames: 345-350
- Categories: manipulation
- Explanation: Following another acquisition and movement toward the plate, the gripper opens at frames 345–349 in wrist_cam with the beige toy still outside the plate rim; overhead_cam likewise shows the gripper beside rather than over the plate. This repeats an off-plate release rather than completing placement. The release is still unfolding at the window boundary, so its final resting position and continuation are unknown.
- Recovery: Stop releasing outside the plate, reacquire the toy if necessary, and verify that the entire toy is above the plate interior before opening the gripper; no human intervention is established as necessary.
- Severity: low
- Severity evidence: The visible consequence is another unsuccessful placement beside the plate, with no observed damage; the final landing is not supplied.
- Resetability: immediate
- Resetability evidence: The visible toy and gripper remain over the accessible tabletop, with no demonstrated need for human resetting; the final release outcome remains outside this window.
