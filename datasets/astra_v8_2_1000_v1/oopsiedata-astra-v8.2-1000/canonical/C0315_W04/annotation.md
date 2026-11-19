# Episode: C0315_W04

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: Sorting remains incomplete in this observed window: overhead_cam shows the orange food-shaped item remaining on the table beside the gripper at frames 1050, 1200, 1300 and 1399, with no transfer into either bowl. wrist_cam shows prolonged stationary positioning and intermittent finger movements without visible acquisition or transport. Completion is unconfirmed, rather than a demonstrated completed grasp followed by loss. This outcome is provisional; earlier execution beyond frames 1048–1049 and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1400 | Yes |

## Failure annotations

### Failure 1

- Frames: 1050-1400
- Categories: task_not_attempted
- Explanation: overhead_cam and wrist_cam show sustained unproductive positioning beside the orange item throughout the window, including frames 1050–1151 and 1160–1232. Intermittent finger movements, including frames 1277–1301 and 1375–1391, leave the item on the table without transport or meaningful sorting progress. These movements do not independently establish failed acquisition or hardware malfunction. The stationary pose matches the supplied context frames 1048–1049, supporting continuity across the starting boundary, although the earlier onset is unseen. The unproductive behavior may continue beyond frame 1399; the window ending is not evidence of termination.
- Recovery: Reassess the item's position, align the fingers around its body, and perform a deliberate acquisition with visual confirmation before transporting it to the food bowl; no visible condition requires human intervention.
- Severity: low
- Severity evidence: The observed consequence is delayed and incomplete sorting; neither camera shows damage, a spill, or a meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The item remains accessible on the tabletop and the bowls remain upright, so another attempt requires no environmental reset or human intervention.