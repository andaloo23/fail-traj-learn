# Episode: C0586

## Episode annotation

- Language task: Pick up the block and place it on the cardboard.
- Success label: failure
- Outcome evidence: The green block starts beside the cardboard (frame 0, camera_high). The right gripper approaches and closes beside the block without lifting it (frames 267–330, camera_wrist_right and camera_high), then reopens. At frame 749, camera_high still shows the block off the cardboard, while camera_wrist_right shows the open gripper near it. Placement is not completed; a failed acquisition is visible, although later alignment remains unfinished.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 293 | No |
| 293 | 358 | Yes |
| 358 | 750 | No |

## Failure annotations

### Failure 1

- Frames: 293-358
- Categories: grasp
- Explanation: By frame 293, camera_wrist_right shows the fingers closed beside rather than around the green block. Through frames 310–350, the block remains outside the closed fingers, and camera_high shows no pickup or transport toward the cardboard. The unsuccessful closed-gripper interval ends when the fingers begin reopening at frame 358.
- Recovery: Reopen the fingers, center them on opposite sides of the block at an appropriate height, and close before performing a small verification lift; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt fails to acquire the block; camera_high and camera_wrist_right show no damage, fallen objects, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The block remains accessible on the tabletop and the cardboard remains in place, so another aligned grasp can be attempted without environmental reset or human intervention.