# Episode: C0322_W05

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisionally for this window, no toy is placed on the plate: overhead_cam shows it empty at frames 1400, 1557, 1635 and 1749. wrist_cam shows opening and realignment at frames 1400–1541, closure at frames 1542–1557, and subsequent movement with the beige toy remaining outside the closed fingers on the table at frames 1614–1667. This establishes an unsuccessful acquisition rather than merely unconfirmed completion. No unwanted collision is clearly established. The opening and realignment at this window's start are recovery, so the preceding predicted failure is not automatically continued. Earlier execution beyond the two context frames and later completion are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1558 | No |
| 1558 | 1750 | Yes |

## Failure annotations

### Failure 1

- Frames: 1558-1750
- Categories: grasp
- Explanation: After closing beside the beige toy at frames 1542–1557 in wrist_cam, the robot begins moving and rotating the closed gripper at frame 1558 without acquiring the toy. The toy becomes clearly visible outside the fingers on the tabletop at frames 1614–1667; overhead_cam also shows no transfer onto the plate. The robot subsequently moves away with the fingers closed through frame 1749, without a visible retained toy or renewed acquisition. Initial occlusion limits the precise contact interpretation, but the before/after views support a missed acquisition, not a demonstrated drop. This unsuccessful cycle reaches the window edge; its continuation or recovery afterward is unseen.
- Recovery: Open the gripper, reacquire the toy's position, and align the fingers around its body with clearance from the plate rim; verify retention with a small lift before transferring it onto the plate. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The toy remains on the tabletop, and neither overhead_cam nor wrist_cam establishes damage or a meaningful damage risk from this missed acquisition.
- Resetability: immediate
- Resetability evidence: The plate and toy remain accessible and usable; a corrected acquisition requires no visible environmental reset or human intervention.