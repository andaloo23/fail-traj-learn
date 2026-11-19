# Episode: C0759_W01

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisional for this window: the pink toy is released onto the plate at frames 150–160, but the tan toy is released onto the table beside it at frames 264–270, and the blue toy remains on the table after an empty-handed withdrawal at frames 325–349 (overhead_cam, wrist_cam). The tan toy is also displaced during the initial pink-toy approach at frames 46–49 (wrist_cam). Thus the supplied window shows unsuccessful attempts as well as partial completion; later episode context is unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 46 | No |
| 46 | 50 | Yes |
| 50 | 260 | No |
| 260 | 278 | Yes |
| 278 | 324 | No |
| 324 | 350 | Yes |

## Failure annotations

### Failure 1

- Frames: 46-50
- Categories: collision
- Explanation: During the approach to the pink toy, the neighboring tan toy abruptly tips and shifts away at frames 46–49 in wrist_cam, while overhead_cam shows the gripper descending among the toys. This unintended displacement violates the no-collisions requirement.
- Recovery: Pause, establish clearance from the displaced tan toy, and realign around the pink toy before continuing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The soft toy is displaced on the tabletop; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The displaced toy remains accessible on the table and can be acquired from its new pose without human resetting.

### Failure 2

- Frames: 260-278
- Categories: manipulation
- Explanation: After carrying the tan toy toward the plate, the robot opens its fingers at frames 260–265 and leaves the toy on the tabletop outside the near rim, rather than on the plate; it remains there as the gripper withdraws through frame 277 (wrist_cam, overhead_cam). Possession was established earlier, so this is an unsuccessful placement rather than a failed acquisition.
- Recovery: Reacquire the tan toy, lift it clear of the rim and pink toy, and release it only when fully over the plate; no human intervention appears necessary.
- Severity: low
- Severity evidence: The toy lands on the table beside the plate with no visible damage.
- Resetability: immediate
- Resetability evidence: The toy remains within the accessible workspace, so another acquisition and placement can be attempted without environmental intervention.

### Failure 3

- Frames: 324-350
- Categories: grasp
- Explanation: Following closure near the blue toy at frames 312–324, the robot withdraws with closed, empty fingers and moves toward the plate at frames 325–338 while the blue toy remains on the table (overhead_cam, wrist_cam). It remains empty near the plate through frame 349 rather than correcting the missed acquisition. Whether this behavior continues beyond the window is unknown.
- Recovery: Return with open fingers, align around the blue toy's body, and verify secure acquisition with a small lift before transporting it; no human intervention appears necessary.
- Severity: low
- Severity evidence: The blue toy remains on the tabletop, and no damage is visible; the consequence is a failed acquisition and empty transfer.
- Resetability: immediate
- Resetability evidence: The blue toy is still accessible for an immediate retry without human resetting.