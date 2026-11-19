# Episode: C0391

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image frames 500–600, the robot transfers the green can into the upper tray and withdraws. It subsequently approaches the blue bowl, but remains near it without completing a transfer. At frame 2305, the pink/yellow can and both bowls remain outside their destination trays, and the right tray is empty. The task is visibly incomplete, with sustained stalling rather than a confirmed failed grasp; no completion or recovery is observed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1000 | No |
| 1000 | 2306 | Yes |

## Failure annotations

### Failure 1

- Frames: 1000-2306
- Categories: task_not_attempted
- Explanation: Following the bowl approach and positional adjustments visible in base_image frames 698–900, the gripper settles into an essentially unchanged near-bowl pose by approximately frame 1000. Frames 1100, 1400, 1750, 2100 and 2305 show continued inactivity with only minor adjustments and no discernible acquisition or transfer. This approximately 13-second interval constitutes one continuous stall across the window boundaries. The precise transition from useful alignment to stalling is uncertain; frame 1000 marks the approximate onset supported by the visual checks. No empty withdrawal, loss of possession, hardware malfunction or abnormal termination is established.
- Recovery: Reassess the bowl and gripper alignment, execute a controlled acquisition, and verify retention before transferring the bowl to the right tray; then sort the remaining objects. No human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is prolonged lack of task progress; base_image frames 1000–2305 show no new damage, harmful displacement or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The objects remain accessible and the scene requires no visible environmental resetting; the robot can resume a task-directed attempt without human intervention.