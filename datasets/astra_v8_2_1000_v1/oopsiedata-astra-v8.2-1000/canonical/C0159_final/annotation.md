# Episode: C0159

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: success but side effects
- Outcome evidence: In base_image, both cans are released into the upper blue tray by frame 2400, the blue bowl rests in the right red tray by frame 3498, and both bowls are stacked there with the gripper withdrawn by frame 4400. Frame 4771 confirms the completed arrangement. During withdrawal after the blue-bowl placement, the robot’s hanging cable appears to catch and displace the still-uncollected pink bowl (frames 3400–3500); no damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 3400 | No |
| 3400 | 3500 | Yes |
| 3500 | 4772 | No |

## Failure annotations

### Failure 1

- Frames: 3400-3500
- Categories: collision
- Explanation: In base_image, the hanging cable overlaps the pink bowl during the blue-bowl placement and withdrawal at frames 3300–3400. By frames 3498–3500, the pink bowl has shifted leftward and downward while the gripper withdraws from the blue bowl, rather than intentionally acquiring the pink bowl. This supports unintended contact and displacement, apparently from the cable; the precise contact onset is uncertain between the supplied checks.
- Recovery: Lift and route the gripper and hanging cable clear of the bowls, then reacquire the pink bowl at its updated position and place it in the right tray. Human intervention is not visibly needed.
- Severity: low
- Severity evidence: The pink bowl moves a short distance but stays upright on the table; no breakage, spill, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The displaced bowl remains accessible and usable, so the robot can continue from its updated position without a human reset.