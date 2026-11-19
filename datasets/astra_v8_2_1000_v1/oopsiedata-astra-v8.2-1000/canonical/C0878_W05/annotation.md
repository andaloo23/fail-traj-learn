# Episode: C0878_W05

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: Completion remains unconfirmed in this provisional window outcome. In base_image, the robot acquires the pink can and carries it toward the upper tray (frames 1600–1749), but release is not shown. The green can remains in that tray, both bowls remain on the table, and the right tray remains empty at frame 1749. During acquisition, the nearby blue bowl is displaced and rocks (frames 1432–1590), establishing a local side effect rather than a failed can grasp. Earlier context is limited to frames 1398–1399; later completion is unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1432 | No |
| 1432 | 1551 | Yes |
| 1551 | 1750 | No |

## Failure annotations

### Failure 1

- Frames: 1432-1551
- Categories: collision
- Explanation: In base_image, the blue bowl beside the gripper progressively shifts upward as the robot acquires and reorients the pink can (frames 1432–1548), then rocks visibly (frames 1551–1590). This incidental displacement does not place the bowl in the right tray and is an unwanted contact side effect. The exact contacting robot surface is partly occluded. Subsequent bowl rocking is a consequence, not evidence that the later can transport is itself failing.
- Recovery: Maintain clearance from the bowl while lifting and transporting the can, allow the bowl to settle, then acquire it deliberately for placement in the right tray; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The bowl remains on the tabletop without visible breakage, spilled contents, or other damage in base_image through frame 1749.
- Resetability: immediate
- Resetability evidence: The displaced bowl remains accessible and upright after settling; the robot can continue from its updated position without a human reset.