# Episode: C0428

## Episode annotation

- Language task: Pick up the block and place it on the cardboard.
- Success label: success but suboptimal
- Outcome evidence: The first grasp misses: camera_wrist_right shows the fingers closing short of the green block at frames 199–225 and withdrawing empty at frames 228–254, while camera_high shows the block remaining on the table. A later grasp succeeds, with the block carried toward the cardboard at frames 473–530 in camera_wrist_right and camera_high. The fingers release it at frames 576–584; camera_high confirms the block remains on the cardboard after withdrawal through frame 749.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 199 | No |
| 199 | 256 | Yes |
| 256 | 750 | No |

## Failure annotations

### Failure 1

- Frames: 199-256
- Categories: grasp
- Explanation: In camera_wrist_right, the fingers close short of the block at frames 199–225 without enclosing it, then withdraw empty at frames 228–254. camera_high confirms that the block stays at its original tabletop location, so this acquisition attempt does not advance the task.
- Recovery: Reopen the gripper, realign the fingers around opposing sides of the block, and close before verifying possession with a small lift; no human intervention is needed.
- Severity: low
- Severity evidence: The block remains on the table, with no visible damage or harmful displacement in camera_high or camera_wrist_right.
- Resetability: immediate
- Resetability evidence: The block and cardboard remain accessible and usable; another grasp can be attempted without environmental resetting or human intervention.