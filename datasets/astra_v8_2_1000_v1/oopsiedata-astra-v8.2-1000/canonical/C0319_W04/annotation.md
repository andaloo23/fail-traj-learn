# Episode: C0319_W04

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image frames 1050–1225, the robot engages the pink can and begins lifting it toward the upper blue tray. In frames 1226–1254, the can rotates downward and settles outside the tray beside the blue bowl; the gripper subsequently withdraws without it. At frame 1399, the pink can remains outside the upper tray, both bowls remain on the table, and the right tray is empty. This is a visibly unsuccessful can transfer, not merely unconfirmed completion. The outcome is provisional for this window; earlier execution beyond the supplied context and later recovery are not visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1226 | No |
| 1226 | 1283 | Yes |
| 1283 | 1400 | No |

## Failure annotations

### Failure 1

- Frames: 1226-1283
- Categories: grasp
- Explanation: In base_image frame 1226, the pink can begins rotating downward relative to the lifting gripper. Through frames 1229–1254 it moves away from the fingers and settles beside the blue bowl, outside the upper tray. The gripper continues withdrawing empty through frame 1282, establishing unsuccessful retention and transfer. The images do not establish the mechanical cause of the loss.
- Recovery: Re-localize the pink can, approach its current position with clearance from the bowl and tray, secure a stable grasp, and verify retention before transporting it fully over the upper tray. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The can remains on the tabletop, with no visible spill, newly established damage, or meaningful damage risk; the observed consequence is an unsuccessful transfer.
- Resetability: immediate
- Resetability evidence: The can remains accessible beside the upper tray and can be approached again without a human reset; its changed pose requires re-localization rather than environmental restoration.