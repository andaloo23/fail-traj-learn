# Episode: C0505

## Episode annotation

- Language task: put the pineapple in the purple bowl
- Success label: success but side effects
- Outcome evidence: The robot lifts and carries the pineapple in frames 80–145 (left, right, wrist), then releases it into the purple bowl at frames 151–154 (wrist, left). It remains in the bowl through frame 399 (wrist, left). During transport, the robot also displaces the unrelated orange-checkered tray and its contents, visibly changing their position between frames 104 and 105 (left, right).

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 104 | No |
| 104 | 108 | Yes |
| 108 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 104-108
- Categories: collision
- Explanation: While carrying the pineapple past the orange-checkered tray, the robot or carried object contacts the tray area and shifts the tray and its contents; the displacement is visible across frames 104–107 in left and right, with close proximity visible in wrist. This disturbs unrelated objects rather than advancing the requested placement; the precise contacting part is not clearly resolved.
- Recovery: Lift the held pineapple clear of the tray and continue along a collision-free path to the purple bowl; a person can restore the tray's original position if needed.
- Severity: low
- Severity evidence: The tray and contents shift but remain on the table; no breakage, spill, or other meaningful damage is visible in left and right at frames 105–108.
- Resetability: minor_reset
- Resetability evidence: Restoring the displaced tray and its contents would require only a straightforward repositioning on the table, with no repair or difficult retrieval visible.