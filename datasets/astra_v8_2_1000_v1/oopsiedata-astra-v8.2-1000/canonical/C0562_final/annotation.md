# Episode: C0562

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Only the blue toy is placed on the plate, visible in overhead_cam and wrist_cam at frames 724–730 and still there at frame 899; the pink and cream toys remain on the table in overhead_cam. Earlier attempts release the blue toy outside the plate (frames 116–124 and 473–478, both cameras). Thus the observed task is incomplete, with visibly unsuccessful placements rather than merely unconfirmed completion. No unwanted collision or damage is clearly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 116 | No |
| 116 | 129 | Yes |
| 129 | 441 | No |
| 441 | 479 | Yes |
| 479 | 900 | No |

## Failure annotations

### Failure 1

- Frames: 116-129
- Categories: manipulation
- Explanation: After lifting and transporting the blue toy, the robot opens its gripper while the toy is still outside the plate at frames 116–120; it falls onto the tabletop and settles beside the plate at frames 122–128 (overhead_cam and wrist_cam). This release fails to place the toy on the intended destination; the images do not establish why it was released there.
- Recovery: Reacquire the blue toy, carry it fully over the plate, lower it, and release only after checking placement alignment; no human intervention is needed.
- Severity: low
- Severity evidence: The toy falls a short distance onto the table and remains accessible; neither camera shows damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains on the unobstructed tabletop beside the plate, allowing another acquisition without environmental intervention.

### Failure 2

- Frames: 441-479
- Categories: manipulation
- Explanation: With the blue toy held over the plate at frames 429–440, the robot carries it away across the rim and out over the tabletop during frames 441–470, then opens its fingers and releases it onto the table at frames 473–478 (overhead_cam and wrist_cam). Established object control is used to move away from the destination and complete another off-plate placement.
- Recovery: Regrasp the toy and return it directly over the plate with sufficient clearance, then lower and release inside the rim; no human intervention is needed.
- Severity: low
- Severity evidence: The blue toy lands on the tabletop without visible damage; the plate and other toys remain usable and undisturbed.
- Resetability: immediate
- Resetability evidence: The released toy is still reachable on the table, so another attempt requires no human reset or repair.