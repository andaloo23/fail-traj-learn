# Episode: C0391_W06

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image frames 1750, 1850, 1950 and 2099, the robot remains at the blue bowl without discernible acquisition or transfer. Both bowls and the pink/yellow can remain outside their destination trays; the green can is in the upper tray and the right tray remains empty. Completion is not observed, with sustained stalling visible rather than a confirmed failed grasp. This outcome is provisional for this window; earlier execution beyond the context frames and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1750 | 2100 | Yes |

## Failure annotations

### Failure 1

- Frames: 1750-2100
- Categories: task_not_attempted
- Explanation: Across base_image frames 1750–2099, the gripper stays in essentially the same pose at the blue bowl for approximately 3.5 seconds, without productive alignment, acquisition or object transfer. This supports sustained stalling independently of the prior prediction, but does not establish a grasp failure or hardware malfunction. Context frames 1748–1749 show the same pose, consistent with continuity at the starting boundary; the earlier onset is unavailable and the stall may continue beyond this window.
- Recovery: Reassess the bowl and gripper alignment, make a controlled acquisition, and verify retention before transferring the bowl to the right tray; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is delayed task progress; base_image frames 1750–2099 show no new damage, displaced objects or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The scene remains unchanged and the objects remain accessible, so another task-directed attempt requires no visible environmental reset or human intervention.