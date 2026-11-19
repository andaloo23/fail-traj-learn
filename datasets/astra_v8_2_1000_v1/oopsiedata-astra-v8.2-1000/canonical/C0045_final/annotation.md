# Episode: C0045

## Episode annotation

- Language task: Stack the small teal block on top of the yellow rectangle.
- Success label: failure
- Outcome evidence: The robot eventually carries the teal block toward the yellow rectangle (frames 99–150, wrist_cam and left_base_cam), but releases it beside rather than on top of the rectangle (frames 222–226, wrist_cam). After withdrawal, the blocks remain unstacked at frame 240 in wrist_cam and right_base_cam. This is a visibly unsuccessful placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 36 | No |
| 36 | 44 | Yes |
| 44 | 222 | No |
| 222 | 241 | Yes |

## Failure annotations

### Failure 1

- Frames: 36-44
- Categories: grasp
- Explanation: Following the initial finger closure around the teal block at frames 33–35, the gripper lifts and opens without retaining it at frames 36–43; wrist_cam shows the block remaining below the fingers, while left_base_cam shows the hand withdrawing without the block. The acquisition attempt does not advance the stack.
- Recovery: Realign the open fingers around opposite sides of the teal block, close securely, and verify retention with a small lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The block remains on the tabletop, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The target remains accessible and the scene requires no intervention before another grasp attempt.

### Failure 2

- Frames: 222-241
- Categories: manipulation
- Explanation: After successfully transporting the teal block, the robot opens its fingers at frames 222–225 with the block beside the yellow rectangle rather than over its top surface. Frames 226–240 in wrist_cam and right_base_cam show the gripper withdrawing and the teal block left on the tabletop next to the rectangle, so the intended stack is not formed.
- Recovery: Regrasp the teal block, lift it clear of the rectangle, center it above the rectangle’s top surface, lower it onto that surface, and release only after confirming support; no human intervention is needed.
- Severity: low
- Severity evidence: The unsuccessful placement leaves both blocks intact on the table; no damage or hazardous displacement is visible.
- Resetability: immediate
- Resetability evidence: Both required objects remain accessible in usable poses, allowing another attempt without an environmental reset.