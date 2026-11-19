# Episode: C0319_W07

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: Provisional for this window: base_image frames 2100–2449 show the robot moving the light-blue bowl together with the adjacent can cluster toward the upper blue tray, rather than separating the bowl for the right tray. By frames 2384–2449, the bowl is over the upper tray, the pink bowl remains on the table, and the right red tray remains empty. Completion is not visible; the mixed-object transport is visibly inconsistent with the requested sorting, although final release is unconfirmed. Earlier execution beyond the two context frames and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 2100 | 2255 | No |
| 2255 | 2450 | Yes |

## Failure annotations

### Failure 1

- Frames: 2255-2450
- Categories: sequencing_semantic
- Explanation: In base_image, beginning at frame 2255 and becoming clear through frames 2261–2300, the light-blue bowl moves with the can cluster toward the upper tray. Frames 2338–2449 show the bowl carried over that tray instead of toward the right tray required for bowls. This mixed-object transport fails to preserve the requested sorting. The exact grip/contact arrangement is occluded, so a separate grasp failure or collision is not established. No corrective separation is visible before the window ends; the behavior may continue beyond it.
- Recovery: Separate the bowl from the cans using controlled, supported placement, then acquire the bowl individually and move it to the right tray; place only cans in the upper tray. Human intervention is not visibly required.
- Severity: low
- Severity evidence: The visible consequence is incorrect sorting/transport; base_image frames 2255–2449 show no spill, breakage, or other meaningful damage.
- Resetability: immediate
- Resetability evidence: The objects remain accessible on or above the tabletop trays, allowing corrective sorting without a visible need for human resetting; final release and the precise support arrangement remain unconfirmed.