# Episode: C0401

## Episode annotation

- Language task: stack the bowls
- Success label: success but side effects
- Outcome evidence: The turquoise bowl is nested inside the pale lavender bowl after bowl handling (left and top, frames 1050–1110), and the bowls remain together on the tabletop at frame 1999 (right and top). They already appear nested initially (left, frame 60; top, frame 0), so a newly created stack is not established, but the requested final arrangement is visible. The robot also displaces a red fruit-shaped object, repeatedly handles an unrelated plush toy, and places an orange object inside the bowls (left and top, frames 150, 450–600, 1380–1400, and 1800–1999). It briefly tips the bowls before restoring their resting position (right and top, frames 1525–1710).

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 142 | No |
| 142 | 155 | Yes |
| 155 | 210 | No |
| 210 | 667 | Yes |
| 667 | 1113 | No |
| 1113 | 1400 | Yes |
| 1400 | 1525 | No |
| 1525 | 1547 | Yes |
| 1547 | 1740 | No |
| 1740 | 2000 | Yes |

## Failure annotations

### Failure 1

- Frames: 142-155
- Categories: collision
- Explanation: The moving gripper pushes the unrelated red fruit-shaped object away from its previous position beside the bowls (left and top, frames 142–154). This incidental displacement does not advance stacking.
- Recovery: Move clear of the displaced object and approach the bowls along an unobstructed path; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The object remains on the tabletop without visible damage or a fall.
- Resetability: immediate
- Resetability evidence: The displaced object does not visibly obstruct the bowls, so another attempt requires no environmental reset.

### Failure 2

- Frames: 210-667
- Categories: sequencing_semantic
- Explanation: The robot approaches and repeatedly works at the brown plush toy rather than a bowl (left and right, frames 210–420), transports it (left and top, frames 450–570), and leaves it beside the bowls by frame 600. Further toy-directed adjustments occur through frames 630–666 before withdrawal. This is one continuous wrong-object episode across the window boundary, not evidence of a bowl-grasp failure.
- Recovery: Leave the plush on the table, identify the bowls and their existing nesting, and perform only the bowl handling needed for a stable stack; no human intervention is visibly required.
- Severity: low
- Severity evidence: The plush is relocated, but no tearing, bowl breakage, or other meaningful damage is visible.
- Resetability: immediate
- Resetability evidence: The toy and bowls remain accessible on the usable tabletop; a corrected attempt needs no human reset.

### Failure 3

- Frames: 1113-1400
- Categories: sequencing_semantic
- Explanation: After withdrawing from the bowls, the robot approaches the unrelated orange fruit-shaped object (left and top, frames 1113–1170), acquires and transports it toward the bowls (frames 1200–1290), then releases it inside the turquoise bowl (frames 1380–1399). This unwanted placement does not advance bowl stacking.
- Recovery: Remove the orange object and return it to a clear tabletop location while preserving the nested bowls, then withdraw; human intervention is not evidently necessary.
- Severity: low
- Severity evidence: The orange object is relocated into the bowl, but no damage, spill, or meaningful damage risk is visible.
- Resetability: minor_reset
- Resetability evidence: Restoring the scene requires the straightforward removal of the orange object from the bowl, which the robot or a person could perform.

### Failure 4

- Frames: 1525-1547
- Categories: manipulation
- Explanation: The right-side gripper tips the already nested bowls into an oblique resting position instead of maintaining their stable arrangement (right and top, frames 1525–1546). The gripper begins backing away at frame 1547; subsequent repositioning is recovery, not a continuation of the failure merely because the tilt persists.
- Recovery: Stabilize the nested bowls, lower their bases flat onto the table, release the rim, and withdraw without disturbing nearby objects; human intervention is not evidently necessary.
- Severity: low
- Severity evidence: The bowls remain together on the tabletop and retain the orange object; no breakage or spill is visible.
- Resetability: immediate
- Resetability evidence: The accessible, intact bowls can be directly stabilized and repositioned without human resetting or repair.

### Failure 5

- Frames: 1740-2000
- Categories: sequencing_semantic
- Explanation: By frame 1740, the gripper is again aligning toward the brown plush rather than the bowls (left and top), continuing its approach through frame 1800. It squeezes and reorients the toy through frames 1860–1999 (left and right), while the bowls remain nested in top. This renewed wrong-object behavior begins before the window seam; the precise transition between withdrawal and approach is less certain than the subsequent manipulation.
- Recovery: Release the plush gently onto a clear tabletop area, withdraw without disturbing the bowls, and verify that the stack is stable before stopping; human intervention is not evidently needed.
- Severity: low
- Severity evidence: The plush is compressed and reoriented, but no tearing, breakage, or other meaningful damage is visible.
- Resetability: immediate
- Resetability evidence: The plush and bowls remain accessible and intact; the robot can release the toy and withdraw without a human environmental reset.