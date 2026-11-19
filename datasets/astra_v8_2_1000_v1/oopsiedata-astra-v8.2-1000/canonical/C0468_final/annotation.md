# Episode: C0468

## Episode annotation

- Language task: Remove the orange toy from the blue bowl.
- Success label: failure
- Outcome evidence: The orange toy is inside the blue bowl initially (frame 0, right_base_cam; frame 6, wrist_cam). The robot approaches and works at the bowl, but the toy repeatedly rolls within it rather than being extracted (frames 65–175, wrist_cam). The gripper then withdraws empty while the toy remains in the bowl (frames 180–194, right_base_cam and left_base_cam), establishing a visibly unsuccessful attempt rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 65 | No |
| 65 | 195 | Yes |

## Failure annotations

### Failure 1

- Frames: 65-195
- Categories: grasp
- Explanation: Beginning around frame 65, the toy rolls and rocks within the bowl during repeated near-object gripper adjustments, without secure acquisition or extraction (frames 65–175, wrist_cam). The bowl also shifts somewhat on the table. The subsequent empty withdrawal confirms failed acquisition: the toy remains in the bowl as the gripper moves away (frames 180–194, right_base_cam and left_base_cam). No secure possession or subsequent drop is established.
- Recovery: Retract clear of the rim, allow the toy to settle, realign the open fingers around the toy rather than the bowl, and retry acquisition before lifting vertically clear of the bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The toy remains contained and the bowl remains upright on the table; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: Despite some bowl displacement, the bowl and toy remain accessible in a valid state for another attempt, with no cleanup or human reset required.