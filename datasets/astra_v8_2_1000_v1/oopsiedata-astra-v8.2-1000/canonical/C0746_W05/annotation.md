# Episode: C0746_W05

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image, the gripper adjusts near the red/yellow can at frames 1400–1579, then withdraws toward the upper blue tray without it (frames 1581–1749). Both cans remain on the table, as do both bowls, and neither tray contains a visibly placed object at frame 1749. This window establishes a failed acquisition, not merely unconfirmed completion; the whole-episode outcome remains provisional because earlier and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1581 | No |
| 1581 | 1750 | Yes |

## Failure annotations

### Failure 1

- Frames: 1581-1750
- Categories: grasp
- Explanation: In base_image, the gripper begins withdrawing from the red/yellow can around frame 1581 after adjusting at it. Across frames 1609–1653, the can becomes clearly separated from the retreating gripper and remains on the tabletop while the empty gripper moves over the upper tray; frame 1749 still shows both cans outside the tray. This establishes unsuccessful acquisition followed by empty transport rather than a completed pickup. No renewed approach is visible before the window boundary; the behavior may continue beyond it.
- Recovery: Return to the can, align the fingers around its visible body, close, and verify that it lifts with the gripper before transporting it to the upper tray; no human intervention is visibly required.
- Severity: low
- Severity evidence: The can remains accessible on the tabletop, with no visible spill, new damage, or disruption to the bowls or trays.
- Resetability: immediate
- Resetability evidence: Another grasp can be attempted directly from the can’s current tabletop position without an environmental reset.