# Episode: C0306

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: success but side effects
- Outcome evidence: In base_image, the green can is deposited in the upper blue tray by frame 107, and both cans are there by frame 258. The blue bowl is placed in the right red tray by frame 346, and the pink bowl is nested with it by frames 408–418; this arrangement remains at frame 457. Completion follows an unsuccessful red-can acquisition and unintended displacement and rocking of the blue bowl during frames 137–165.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 137 | No |
| 137 | 190 | Yes |
| 190 | 458 | No |

## Failure annotations

### Failure 1

- Frames: 137-190
- Categories: grasp, collision
- Explanation: In base_image, while the gripper attempts to acquire the red can, the blue bowl is unintentionally displaced leftward beneath the arm beginning around frame 137 and subsequently rocks during frames 152–165. The gripper withdraws without the red can at frames 144–153, leaving it on the table, then moves over the upper tray through frame 189 without transferring it. This is a failed acquisition with incidental bowl contact; the exact contacting robot component is partly occluded.
- Recovery: Move clear of the bowl, allow it to settle, and realign the open gripper around the red can before closing and verifying retention with a short lift; then transfer it to the upper tray. No human intervention is needed for the visible state.
- Severity: low
- Severity evidence: The can remains on the tabletop and the displaced bowl settles upright; base_image shows no spill, breakage, or other meaningful damage.
- Resetability: immediate
- Resetability evidence: Both objects remain accessible on the table, so another acquisition can be attempted from their updated positions without an environmental reset or human intervention.