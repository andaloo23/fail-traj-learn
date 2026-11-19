# Episode: C0874_W04

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: Provisional for this window: in base_image, frames 1050–1189 show the blue bowl transported to and released in the right red tray, with the cans visible in the upper blue tray. Frames 1238–1334 show an attempted acquisition beside the pink bowl; frames 1346–1399 show the gripper moving away empty toward the red tray while the pink bowl remains on the table. Thus the task remains incomplete with a visible failed acquisition, not merely unconfirmed completion. Earlier context is limited to frames 1048–1049, and later recovery or completion is not supplied.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1293 | No |
| 1293 | 1400 | Yes |

## Failure annotations

### Failure 1

- Frames: 1293-1400
- Categories: grasp
- Explanation: In base_image, beginning at frame 1293 the fingers close beside the pink bowl without capturing its rim; by frames 1306–1334 the gripper is closed and the bowl remains stationary. Frames 1346–1399 show the empty gripper moving toward the right tray without the pink bowl, confirming failed acquisition. No successful reacquisition is visible; the unsuccessful sequence may continue beyond this window.
- Recovery: Return to the pink bowl with the gripper open, align the fingers across its rim, and verify secure acquisition with a small lift before transporting it to the right tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The pink bowl remains upright on the table, and no damage, spill, or harmful collision is visible in base_image through frame 1399.
- Resetability: immediate
- Resetability evidence: The missed bowl remains accessible in its original table location, so another acquisition attempt requires no environmental reset or human intervention.