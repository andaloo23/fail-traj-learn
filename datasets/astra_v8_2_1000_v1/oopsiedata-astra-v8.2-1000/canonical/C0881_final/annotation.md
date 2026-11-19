# Episode: C0881

## Episode annotation

- Language task: Pick green block and place on cardboard.
- Success label: success but suboptimal
- Outcome evidence: In exterior_cam, the robot acquires the green block and carries it away from its original position (frames 85–113). It then makes an extended detour to the left of the cardboard before returning (frames 118–289). At frames 333–339, the gripper withdraws upward and the green block remains on the far end of the cardboard, supporting completed placement. No damage or unrelated-object disturbance is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 118 | No |
| 118 | 256 | Yes |
| 256 | 340 | No |

## Failure annotations

### Failure 1

- Frames: 118-256
- Categories: manipulation
- Explanation: After bringing the held green block near the cardboard at frames 110–117, the robot carries it away toward the foreground and left, then repeatedly changes its height and orientation beside the cardboard rather than placing it (exterior_cam, frames 118–255). The extended off-target transport does not advance placement; the block remains retained, with no visible drop. A sustained return toward the placement area begins at approximately frame 256.
- Recovery: Retain the block securely, align it above the cardboard with a direct clearance-preserving motion, lower it onto the surface, and release before withdrawing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is delayed placement; exterior_cam shows no dropped block, damage, or unwanted collision during frames 118–255.
- Resetability: immediate
- Resetability evidence: The block remains in the gripper and the cardboard remains available, so placement can be resumed without resetting the environment or requiring human intervention.