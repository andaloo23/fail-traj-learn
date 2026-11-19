# Episode: C0759_W02

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisional for this window: the blue toy is acquired and transported at frames 408–450 but released outside the plate at frames 502–518; a subsequent acquisition leaves it on the table as the gripper withdraws empty at frames 571–609 (overhead_cam, wrist_cam). At frame 699, the pink toy is on the plate, the blue toy remains on the table, and handling of the tan toy is unfinished. Completion is therefore not visible, with actual failed attempts also established. Earlier context is limited to frames 348–349, which do not independently establish the previously reported missed grasp; the brief initial pause followed by renewed approach is not labeled a continuing failure. Later context is unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 502 | No |
| 502 | 532 | Yes |
| 532 | 571 | No |
| 571 | 636 | Yes |
| 636 | 700 | No |

## Failure annotations

### Failure 1

- Frames: 502-532
- Categories: manipulation
- Explanation: After visibly carrying the blue toy toward the plate at frames 413–450, the robot opens its fingers at frames 502–510 while the toy is outside the near rim. The toy falls onto the tabletop and remains there during withdrawal at frames 513–531, rather than being placed on the plate (overhead_cam, wrist_cam). A new approach begins at frame 532.
- Recovery: Reacquire the blue toy, lift it clear of neighboring toys and the rim, and position it fully over an unoccupied portion of the plate before releasing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The soft toy lands on the tabletop; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The blue toy remains accessible on the table for another attempt without environmental resetting.

### Failure 2

- Frames: 571-636
- Categories: grasp
- Explanation: Following closure around the blue toy at frames 558–570, the gripper lifts and moves away empty while the blue toy stays on the tabletop at frames 571–589, clearly visible in overhead_cam and wrist_cam. It continues toward the plate and opens empty at frames 624–633 instead of transporting the toy. Recovery movement away from this empty placement begins at frame 636.
- Recovery: Return to the blue toy with open fingers, align around its body, and verify retention with a small lift before transporting it to the plate; no human intervention appears necessary.
- Severity: low
- Severity evidence: The failed acquisition and empty transfer leave the toy on the table with no visible damage.
- Resetability: immediate
- Resetability evidence: The target remains accessible in the workspace, and no human or environmental reset is required to retry.