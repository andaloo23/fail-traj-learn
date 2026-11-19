# Episode: C0721

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: The robot places the carrot in the green bowl (wrist_cam, frames 177–185) and the pink rabbit in the purple bowl (overhead_cam and wrist_cam, frames 301–306), but then places the orange fruit and brown food-shaped item with the rabbit (wrist_cam, frames 529–536 and 716–723). The blue toy is also placed in the purple bowl at frames 975–980. At frame 1290, wrist_cam shows food and toys still mixed in the purple bowl and only the carrot in the green bowl; this is visible incorrect sorting, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 503 | No |
| 503 | 540 | Yes |
| 540 | 688 | No |
| 688 | 724 | Yes |
| 724 | 1011 | No |
| 1011 | 1291 | Yes |

## Failure annotations

### Failure 1

- Frames: 503-540
- Categories: sequencing_semantic
- Explanation: The robot carries the orange fruit toward the purple bowl containing the pink rabbit (wrist_cam, frames 503–527), then releases it into that bowl (overhead_cam and wrist_cam, frames 529–536). This mixes food with a toy instead of grouping it with the carrot already in the green bowl; acquisition itself succeeds.
- Recovery: Retrieve the orange fruit and place it with the carrot in the green bowl, checking category assignments before release; no human intervention is needed.
- Severity: low
- Severity evidence: The orange fruit remains contained in an upright bowl, with no visible damage or meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: A single straightforward transfer of the misplaced fruit restores the appropriate sorting state; no repair or difficult retrieval is required.

### Failure 2

- Frames: 688-724
- Categories: sequencing_semantic
- Explanation: The robot carries the brown rounded food-shaped item toward the purple bowl (wrist_cam, frames 688–714) and releases it beside the rabbit and orange fruit (overhead_cam and wrist_cam, frames 716–723). Its matching split construction and food-like form support treating it as food, though its exact food identity is unclear; placing it with the rabbit does not separate the categories.
- Recovery: Move the brown food item into the green bowl and correct the earlier misplaced orange fruit; verify the two groups before proceeding. No human intervention is needed.
- Severity: low
- Severity evidence: The item lands inside the bowl without visible breakage, spilling, or other damage.
- Resetability: minor_reset
- Resetability evidence: The newly misplaced item is accessible in the purple bowl and needs only a straightforward transfer.

### Failure 3

- Frames: 1011-1291
- Categories: task_not_attempted
- Explanation: Following withdrawal, the robot remains stationary with an empty gripper throughout frames 1011–1290 in overhead_cam and wrist_cam. The mixed contents remain unchanged for about 19 seconds despite sorting still being incorrect, establishing sustained unproductive stalling rather than a brief pause; the file ending does not establish abnormal termination.
- Recovery: Reinspect both bowls and transfer the orange fruit and brown food item to the green bowl, leaving the two animal toys together in the purple bowl. No human intervention is visibly required.
- Severity: low
- Severity evidence: The stationary interval leaves the task incomplete but produces no additional visible damage or hazard.
- Resetability: immediate
- Resetability evidence: Stalling causes no additional environmental change; the robot can immediately resume correction of the accessible mixed items without an external reset.