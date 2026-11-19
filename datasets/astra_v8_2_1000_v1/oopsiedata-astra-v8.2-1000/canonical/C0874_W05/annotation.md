# Episode: C0874_W05

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: Provisional for this window: base_image frames 1400 and 1749 show cans in the upper blue tray and the blue bowl in the right red tray, but the pink bowl remains on the table. Frames 1640–1749 show a failed acquisition beside the pink bowl followed by empty movement toward the right tray, rather than merely unconfirmed completion. The initial gripper opening and withdrawal over the right tray do not independently establish the preceding report’s claimed grasp failure; the earlier acquisition is not supplied. Later completion is unknown.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1640 | No |
| 1640 | 1750 | Yes |

## Failure annotations

### Failure 1

- Frames: 1640-1750
- Categories: grasp
- Explanation: In base_image, frames 1640–1655 show the fingers closing just left of the pink bowl without capturing its rim. The bowl remains stationary, and frames 1690–1749 show the gripper moving away empty toward the right tray, confirming failed acquisition. The preceding approach and alignment are not labeled failures. This unsuccessful sequence reaches the window boundary and may continue beyond it.
- Recovery: Return with the fingers open, align them across the pink bowl’s rim, and verify possession with a small lift before transporting the bowl to the right tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The pink bowl remains upright and accessible, with no visible damage, spill, or harmful collision in base_image through frame 1749.
- Resetability: immediate
- Resetability evidence: No environmental reset is needed: the missed bowl remains on the table in its original accessible position, allowing another acquisition attempt.