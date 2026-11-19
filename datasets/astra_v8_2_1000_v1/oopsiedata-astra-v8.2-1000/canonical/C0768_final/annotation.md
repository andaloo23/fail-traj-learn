# Episode: C0768

## Episode annotation

- Language task: Pick up the block and place it on the cardboard.
- Success label: failure
- Outcome evidence: At frame 0, camera_high shows the green block beside the cardboard. The robot approaches and adjusts its gripper near the block, but camera_wrist_right shows the fingers withdrawing and reopening without carrying it (frames 267–305). Subsequent small gripper movements do not produce a pickup or transfer. At frames 700–749, camera_high still shows the block beside the empty cardboard, and camera_wrist_right shows it separate from the fingers. This is a visibly unsuccessful acquisition episode, not merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 267 | No |
| 267 | 750 | Yes |

## Failure annotations

### Failure 1

- Frames: 267-750
- Categories: grasp
- Explanation: Following the closing movement near the block in frames 230–265, the gripper begins withdrawing without the block at frame 267 and reopens in frames 277–305 (camera_wrist_right); camera_high confirms the block remains at the acquisition location. Repeated small finger and wrist movements continue near it, with no established possession or transport through frame 749. The block remains beyond the effective finger grasp rather than being secured between them; the underlying cause is not visible.
- Recovery: Open the fingers, reposition them to straddle opposing sides of the block at an appropriate height, then close and verify a secure pickup with a short lift before moving to the cardboard. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The failed acquisition prevents task completion, but the block remains on the tabletop and no damage or meaningful damage risk is visible in camera_high or camera_wrist_right.
- Resetability: immediate
- Resetability evidence: The block and cardboard remain accessible and usable; another aligned grasp can be attempted without a human or environmental reset.