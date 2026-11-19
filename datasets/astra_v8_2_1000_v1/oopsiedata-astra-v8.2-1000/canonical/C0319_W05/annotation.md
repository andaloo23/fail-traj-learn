# Episode: C0319_W05

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image frames 1400–1496, the gripper approaches the cans beside the upper blue tray, then makes small adjustments around them. During frames 1639–1689, the blue tray shifts and rotates and the nearby blue bowl moves left during the interaction. At frame 1749, both bowls remain outside the empty right tray, and completed can placement is not confirmed. This is a provisional incomplete outcome for this window, with an observed local side effect rather than a confirmed failed acquisition; the gripper has not clearly withdrawn empty. Earlier execution beyond frames 1398–1399 and later completion are not visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1639 | No |
| 1639 | 1722 | Yes |
| 1722 | 1750 | No |

## Failure annotations

### Failure 1

- Frames: 1639-1722
- Categories: collision
- Explanation: In base_image frames 1639–1689, while the gripper works at the cans along the blue tray's left edge, the tray visibly shifts and rotates and the adjacent blue bowl shifts left, away from its intended right-hand destination. The robot remains engaged in this crowded area through frame 1721 rather than clearing the displaced objects. This is unintended displacement during the can interaction; the exact contact chain is partly occluded. From frame 1722, upward withdrawal begins, so the continuing displaced state is not itself labeled as further failure.
- Recovery: Lift clear of the tray rim and bowl, re-localize the displaced objects, and approach an individual can with sufficient clearance before verifying a secure grasp and transferring it into the upper tray. No human intervention is visibly required.
- Severity: low
- Severity evidence: The tray and bowl move slightly but remain upright and on the table; base_image frame 1749 shows no visible spill, breakage, or meaningful damage.
- Resetability: immediate
- Resetability evidence: All objects remain accessible on the tabletop, allowing another approach using their updated positions without a human reset; precise restoration of the tray's original pose is not visibly necessary.