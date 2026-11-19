# Episode: C0785_W04

## Episode annotation

- Language task: pick up the ductape and put it in the green bowl
- Success label: failure
- Outcome evidence: Completion is provisional and unconfirmed in this window, rather than a visibly failed pickup: left and top show approach to the blue tape roll at frames 1166-1274, acquisition and transport at frames 1284-1335, and lowering into the green bowl at frames 1350-1399. At frame 1399, left and right show the roll within the bowl's rim, but the gripper remains engaged and a completed release is not clearly established. Initial sustained inactivity is visible at frames 1050-1165 in left, right and top. Earlier context is limited to frames 1048-1049; later placement confirmation is unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1166 | Yes |
| 1166 | 1400 | No |

## Failure annotations

### Failure 1

- Frames: 1050-1166
- Categories: task_not_attempted
- Explanation: Across frames 1050, 1080, 1110, 1140 and 1165 in left, right and top, the robot holds near the rolls with small pose adjustments but no sustained approach, acquisition or object displacement. This approximately four-second interval is persistently unproductive rather than a failed grasp. Sustained approach begins at frame 1166 and becomes clear through frames 1169-1175. The similar posture in context frames 1048-1049 leaves the exact onset before this window unresolved; the preceding prediction does not establish that these stationary actions advanced the task.
- Recovery: Resume a target-directed approach, align the gripper around the blue tape roll, acquire it securely, and transfer and release it into the green bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The consequence is delayed progress only; left, right and top through frame 1165 show no damage, displaced objects or harmful contact.
- Resetability: immediate
- Resetability evidence: Both rolls and the bowl remain available in their table positions at frame 1165, so another attempt requires no environmental reset or human intervention.