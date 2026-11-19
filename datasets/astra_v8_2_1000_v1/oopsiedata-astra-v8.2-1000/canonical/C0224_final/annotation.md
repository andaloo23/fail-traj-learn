# Episode: C0224

## Episode annotation

- Language task: stack the yellow block on the blue blocks
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot grasps and lifts the foreground yellow block in frames 27–39, but carries it toward the bowl and lowers it among the bowl contents in frames 45–52 rather than onto the adjacent blue blocks. At frame 69, the blue blocks remain bare and the gripper remains at the bowl. This is a visibly wrong-destination attempt; release and any subsequent completion are unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 45 | No |
| 45 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 45-70
- Categories: sequencing_semantic
- Explanation: In right_shoulder_cam, beginning at frame 45 the robot transports the acquired yellow block toward the bowl, then lowers it into the bowl contents by frame 52 and remains there through frame 69. This uses the wrong destination instead of stacking on the paired blue blocks visible on the table. The images do not clearly establish whether the block is released.
- Recovery: Lift the yellow block clear of the bowl if it is still securely held; otherwise reacquire it after checking its position, then align it over the paired blue blocks, lower it onto their top surfaces, and release. No human intervention is visibly required.
- Severity: low
- Severity evidence: The block is diverted into a bowl of other blocks, but no damage, spill, or meaningful damage risk is visible in right_shoulder_cam through frame 69.
- Resetability: immediate
- Resetability evidence: The yellow block remains accessible at the bowl, and the intended blue supports remain in place; no environmental repair or human reset is visibly necessary before a corrected attempt.