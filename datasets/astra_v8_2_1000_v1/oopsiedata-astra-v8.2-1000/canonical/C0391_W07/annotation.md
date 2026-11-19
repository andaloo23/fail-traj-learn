# Episode: C0391_W07

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image frames 2100, 2200 and 2305, the green can is in the upper tray, but the pink/yellow can and both bowls remain outside their destination trays, and the right tray is empty. The robot stays at the blue bowl without discernible acquisition or transfer throughout this window. Completion is unconfirmed, with visible unproductive inactivity rather than a confirmed failed grasp. This outcome is provisional for the supplied window; earlier execution beyond frames 2098–2099 and any later behavior are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 2100 | 2306 | Yes |

## Failure annotations

### Failure 1

- Frames: 2100-2306
- Categories: task_not_attempted
- Explanation: Throughout base_image frames 2100–2305, the gripper remains in essentially the same pose at the blue bowl for approximately 2.05 seconds, with no discernible alignment progress, acquisition or transfer. This sustained inactivity does not advance the sorting task. Context frames 2098–2099 show the same pose, supporting continuity at the starting boundary, though the earlier onset is not visible. No recovery appears before the window ends; continuation beyond it is unknown, and the boundary does not establish abnormal termination.
- Recovery: Reassess the bowl and gripper alignment, resume a controlled acquisition, and verify retention before transferring the bowl to the right tray; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is delayed task progress; base_image frames 2100–2305 show no new damage, object displacement or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The objects and trays remain accessible and unchanged, so resuming task-directed action requires no visible environmental reset or human intervention.