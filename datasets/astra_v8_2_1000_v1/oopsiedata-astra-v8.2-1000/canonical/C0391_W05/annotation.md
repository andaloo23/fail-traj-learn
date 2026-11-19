# Episode: C0391_W05

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image frames 1400, 1500, 1600 and 1749, the gripper stays at the blue bowl without discernible acquisition or transfer. Both bowls and the pink/yellow can remain outside their destination trays; the green can is in the upper tray and the right tray is empty. The task remains incomplete in this window, with visible sustained stalling rather than a confirmed failed grasp. This label is provisional because earlier execution beyond the supplied context frames and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1750 | Yes |

## Failure annotations

### Failure 1

- Frames: 1400-1750
- Categories: task_not_attempted
- Explanation: Throughout base_image frames 1400–1749, the robot holds essentially the same pose at the blue bowl for approximately 3.5 seconds, with slight adjustments but no discernible acquisition, transfer or productive alignment progress. This independently supports sustained stalling, not a demonstrated grasp failure or hardware issue. Context frames 1398–1399 show the same pose, consistent with continuity across the starting boundary, but the earlier onset is unavailable; the stall may also continue beyond this window.
- Recovery: Reassess the bowl and gripper alignment, perform a controlled acquisition, and verify retention before transferring the bowl to the right tray; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is delayed task progress; base_image frames 1400–1749 show no new damage, object displacement or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The objects remain accessible and unchanged, so another task-directed attempt requires no visible environmental reset or human intervention.