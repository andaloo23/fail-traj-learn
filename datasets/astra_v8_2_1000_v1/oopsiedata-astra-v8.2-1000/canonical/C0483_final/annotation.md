# Episode: C0483

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image, the green can is successfully transferred to the upper blue tray by frames 127–156. Attempts to acquire the pink can leave it on the table while the gripper withdraws empty (frames 180–203 and 281–300). At frame 387, the pink can and both bowls remain outside their designated trays, and the right red tray is empty. Thus the task is visibly incomplete, with failed acquisitions rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 180 | No |
| 180 | 245 | Yes |
| 245 | 281 | No |
| 281 | 341 | Yes |
| 341 | 380 | No |
| 380 | 388 | Yes |

## Failure annotations

### Failure 1

- Frames: 180-245
- Categories: grasp
- Explanation: In base_image, after contacting and slightly shifting the pink can at frames 173–179, the gripper separates from it empty beginning at frame 180. It then travels to and operates over the upper tray without the can (frames 193–244), leaving the target on the table and making no transfer.
- Recovery: Return to the pink can, align the fingers around its actual width, and verify secure acquisition with a small lift before transporting it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The can remains on the tabletop; no new damage, spill, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The target remains accessible for another grasp, with no environmental reset or human intervention required.

### Failure 2

- Frames: 281-341
- Categories: grasp
- Explanation: In base_image, the second approach ends with the fingers closing beside the pink can at frames 281–285 without acquiring it. The robot withdraws empty at frames 291–300 and again moves over the upper tray through frame 340 while the pink can stays on the table.
- Recovery: Re-localize the pink can and adjust the grasp position before retrying; confirm that the can follows the gripper before beginning transport. Human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The unsuccessful acquisition wastes motion but causes no visible damage or spill.
- Resetability: immediate
- Resetability evidence: The can remains in an accessible tabletop position, so another attempt needs no scene reset.

### Failure 3

- Frames: 380-388
- Categories: grasp
- Explanation: In base_image, the third attempt shifts the pink can at frames 372–379, but the fingers pull away without retaining it beginning at frame 380. By frames 383–387, the empty fingers are separated from the can, which remains on the table.
- Recovery: Reopen and reposition the fingers to surround the can securely, then perform a short verification lift before transport; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only acquisition fails; no new damage or hazardous consequence is visible.
- Resetability: immediate
- Resetability evidence: The pink can remains reachable on the table, and no cleanup, repair, or manual repositioning is visibly needed.