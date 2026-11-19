# Episode: C0922

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Frame 0 in overhead_cam and wrist_cam shows three toys outside the plate. The blue toy is placed on the plate by frames 825–840, but the pink toy is pushed off the table at frames 440–447. The tan toy is eventually released at the plate's outer rim at frames 1300–1320, rather than clearly inside it. Frame 1467 in overhead_cam does not show all three toys on the plate; this is an observed failed episode, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 68 | No |
| 68 | 108 | Yes |
| 108 | 180 | No |
| 180 | 452 | Yes |
| 452 | 925 | No |
| 925 | 988 | Yes |
| 988 | 1088 | No |
| 1088 | 1150 | Yes |
| 1150 | 1300 | No |
| 1300 | 1326 | Yes |
| 1326 | 1468 | No |

## Failure annotations

### Failure 1

- Frames: 68-108
- Categories: grasp
- Explanation: After closing near the blue toy, the gripper moves away without acquiring it, then opens near the plate at frames 101–108. The before/after views in wrist_cam and overhead_cam, including the blue toy still outside the plate at frame 475, establish the missed acquisition.
- Recovery: Reobserve the blue toy, center the open fingers around its body, and verify a small lift before transferring it; no human intervention is needed.
- Severity: low
- Severity evidence: The toy remains available on the tabletop, with no visible damage.
- Resetability: immediate
- Resetability evidence: A revised grasp can be attempted without resetting the scene.

### Failure 2

- Frames: 180-452
- Categories: grasp, collision
- Explanation: In wrist_cam and overhead_cam, the open gripper repeatedly displaces the pink toy along the tabletop rather than securing it, visible from frames 180–230 onward. Continued contact drives it toward the table edge through frames 380–435, and it falls off at frames 440–447. This prevents its placement and violates the collision constraint.
- Recovery: Stop pushing and have a person retrieve the pink toy once the robot is stationary; then reobserve it and use a centered grasp with lift verification before transfer.
- Severity: low
- Severity evidence: A soft toy falls to the floor; no damage or collision with vulnerable equipment is visible.
- Resetability: minor_reset
- Resetability evidence: The pink toy must be retrieved from beside the table and returned to the workspace; no repair or difficult obstruction is shown.

### Failure 3

- Frames: 925-988
- Categories: grasp
- Explanation: At frames 925–937 in wrist_cam, the gripper closes short of the tan toy and moves away empty while the toy remains on the table. It continues to the plate and opens at frames 980–987 without delivering the toy, also supported by overhead_cam.
- Recovery: Return to the tan toy and align the fingers around its body rather than in front of it; verify possession before moving toward the plate. No human intervention is needed.
- Severity: low
- Severity evidence: The attempt makes no placement progress and causes no visible damage.
- Resetability: immediate
- Resetability evidence: The tan toy remains accessible for another grasp without environmental intervention.

### Failure 4

- Frames: 1088-1150
- Categories: grasp
- Explanation: Following another closure beside the tan toy, wrist_cam frames 1088–1095 show the gripper withdrawing without the toy. It again travels to the plate and opens at frames 1140–1148; overhead_cam and its reappearance on the table at frames 1190–1210 confirm the tan toy was not transferred.
- Recovery: Reestimate the toy's position and choose a body grasp with both fingers straddling it; confirm retention during a short vertical lift. No human intervention is needed.
- Severity: low
- Severity evidence: This is another empty transfer, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The target remains on the usable tabletop and can be immediately reattempted.

### Failure 5

- Frames: 1300-1326
- Categories: manipulation
- Explanation: After acquiring and transporting the tan toy at frames 1243–1299, the robot opens its fingers at the outside edge of the plate. In wrist_cam frames 1304–1320, much of the toy lies outside the rim on the tabletop as the gripper withdraws, rather than being placed securely on the plate; overhead_cam supports the edge placement.
- Recovery: Regrasp the tan toy, lift it clear of the rim, and lower it into an unoccupied area inside the plate before releasing; no human intervention is needed for this correction.
- Severity: low
- Severity evidence: The toy remains supported beside the plate with no visible damage.
- Resetability: immediate
- Resetability evidence: The toy is accessible at the rim and needs no human reset before corrective manipulation.