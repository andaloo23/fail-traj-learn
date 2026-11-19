# Episode: C0391_W04

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image frames 1050, 1150, 1250 and 1399, the gripper remains at the blue bowl without a discernible acquisition or transfer. Both bowls and the pink/yellow can remain outside their destination trays; the green can is in the upper tray and the right tray is empty. Completion is unconfirmed in this window, with sustained lack of progress rather than a visibly completed failed grasp. This outcome is provisional; earlier execution beyond the two context frames and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1400 | Yes |

## Failure annotations

### Failure 1

- Frames: 1050-1400
- Categories: task_not_attempted
- Explanation: Across base_image frames 1050–1399, the robot maintains essentially the same near-bowl pose for approximately 3.5 seconds, with only minute adjustments and no discernible progress toward acquisition or placement. This sustained unproductive interval supports stalling, not a confirmed grasp failure or hardware malfunction. The preceding prediction marked its interval No, but the current images independently show continued inactivity; the actual onset before this window and continuation after it remain uncertain.
- Recovery: Reassess the bowl and gripper alignment, then execute a controlled acquisition and verify retention before transferring the bowl to the right tray; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is delayed task progress; base_image frames 1050 and 1399 show no new damage, displacement or supported damage risk.
- Resetability: immediate
- Resetability evidence: The objects remain accessible in unchanged positions, so the robot can resume a task-directed attempt without environmental resetting or human intervention.