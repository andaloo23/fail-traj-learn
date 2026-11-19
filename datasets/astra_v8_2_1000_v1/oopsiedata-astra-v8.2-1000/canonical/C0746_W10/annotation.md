# Episode: C0746_W10

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image, frames 3150 and 3499 show the green can in the upper blue tray, the red-and-silver can still on the table, and both bowls outside the empty right tray. The gripper closes beside the remaining can and then moves away empty toward the upper tray (frames 3285–3499), establishing a failed acquisition rather than merely unconfirmed completion. This outcome is provisional for the supplied window; earlier execution beyond the two context frames and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 3150 | 3285 | No |
| 3285 | 3500 | Yes |

## Failure annotations

### Failure 1

- Frames: 3285-3500
- Categories: grasp
- Explanation: In base_image, the fingers draw together beside the red-and-silver can during frames 3210–3240. From frame 3285, the gripper withdraws without the can; frames 3350, 3414 and 3499 show it continuing toward the upper blue tray while the can remains in its original tabletop position. This empty transfer does not advance can placement. The unsuccessful behavior reaches the window boundary, and its continuation beyond that boundary is unknown.
- Recovery: Return to the remaining can, align the fingers around its body, and verify a secure acquisition with a small lift before transferring it to the upper tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The can remains on the table, with no visible new damage, spill, or disturbance to the bowls or trays.
- Resetability: immediate
- Resetability evidence: The target remains accessible in its tabletop position, so another grasp can be attempted without environmental resetting or human intervention.