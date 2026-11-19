# Episode: C0401_W01

## Episode annotation

- Language task: stack the bowls
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window: the bowls remain together near the center in top at frames 0, 200 and 349, with no visible stacking operation. Their overlapping rims already suggest nesting initially, so the intended additional stacking arrangement is unclear. The robot instead displaces a red fruit-shaped object and subsequently works at a brown plush toy, visible in left, right and top. This is a provisional window outcome; later episode context is absent.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 142 | No |
| 142 | 155 | Yes |
| 155 | 210 | No |
| 210 | 350 | Yes |

## Failure annotations

### Failure 1

- Frames: 142-155
- Categories: collision
- Explanation: In left at frames 142-150, the moving gripper pushes the unrelated red fruit-shaped object out of its previous position; top at frames 142-155 confirms its displacement along the arm away from its original location beside the bowls. This incidental contact does not advance stacking.
- Recovery: Move clear of the fruit-shaped object and approach the bowls along an unobstructed path; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The object moves on the tabletop without visible damage or falling off the table.
- Resetability: immediate
- Resetability evidence: The bowls remain accessible and the displaced object stays on the table; another task attempt does not require an environmental reset.

### Failure 2

- Frames: 210-350
- Categories: sequencing_semantic
- Explanation: The gripper approaches the brown plush toy rather than a bowl from frame 210, aligns at its face and loop in left and right at frames 225-250, and closes and moves against it at frames 310-325. Further gripper adjustments continue around the toy through frame 349 while the bowls remain untouched in top. This is wrong-object behavior, regardless of whether a secure grasp is achieved; sustained possession is not established. The behavior may continue beyond the window.
- Recovery: Disengage from the plush toy, identify the bowls and their existing arrangement, then grasp a bowl rim and place it onto the intended receiving bowl if further stacking is needed; no human intervention is visibly required.
- Severity: low
- Severity evidence: The toy is disturbed, but no tearing, breakage or other meaningful damage is visible.
- Resetability: immediate
- Resetability evidence: The toy and bowls remain on the usable tabletop, allowing a corrected bowl-directed attempt without human resetting.