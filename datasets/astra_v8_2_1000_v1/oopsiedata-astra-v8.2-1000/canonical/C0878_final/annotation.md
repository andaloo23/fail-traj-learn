# Episode: C0878

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: success but side effects
- Outcome evidence: In base_image, both cans are in the upper blue tray by frame 2098; the blue bowl is placed in the right red tray by frames 2798–2900, and the pink bowl is subsequently stacked on it by frames 3700–3800. The completed arrangement remains visible at frame 4063 after the empty gripper withdraws. During pink-can acquisition, however, the robot incidentally displaces and rocks the blue bowl (frames 1432–1600), an unintended contact side effect.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1432 | No |
| 1432 | 1551 | Yes |
| 1551 | 4064 | No |

## Failure annotations

### Failure 1

- Frames: 1432-1551
- Categories: collision
- Explanation: In base_image, while the robot acquires and reorients the pink can, the adjacent blue bowl shifts toward the upper part of the table, with displacement developing around frames 1432–1500 and clearly visible by frames 1549–1550. This incidental contact moves the bowl away from its original position without deliberately transferring it to the right tray. The exact contacting surface is partly occluded, and the precise onset is subtle. Subsequent rocking and settling through frame 1600 are consequences rather than a separate failure during the successful can transport.
- Recovery: Lift and transport the can with clearance from the bowl, allow the bowl to settle, and then acquire it deliberately from its updated position for placement in the right tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The bowl remains on the tabletop without visible breakage or spilled contents, settles upright, and is later successfully transferred to the right tray in base_image frames 2500–2900.
- Resetability: immediate
- Resetability evidence: The displaced bowl remains accessible and upright after settling, so the robot can continue using its updated position without human intervention or environmental resetting.