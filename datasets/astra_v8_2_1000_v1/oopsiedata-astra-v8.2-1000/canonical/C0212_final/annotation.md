# Episode: C0212

## Episode annotation

- Language task: pull out the block sticking out
- Success label: failure
- Outcome evidence: The protruding orange block is approached and gripped in frames 0–53 (front, wrist). During subsequent movement, surrounding wooden blocks shift and topple rather than remaining stacked (frames 54–80, front, wrist). By frames 82–84 the gripper opens, leaving the orange block still overlapping the disrupted pile; complete extraction is not visible. This is a visibly disrupted extraction attempt, not merely an unconfirmed outcome at recording end.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 54 | No |
| 54 | 85 | Yes |

## Failure annotations

### Failure 1

- Frames: 54-85
- Categories: manipulation
- Explanation: After gripping the orange block, the robot moves it together with surrounding wooden blocks instead of cleanly extracting it: the upper stack starts shifting sideways at frames 54–58 (front, wrist). Blocks subsequently tilt and fall out of alignment at frames 68–80, including a wooden block falling to the right of the pile in front. At frames 82–84 the gripper opens with the orange block still among the displaced blocks.
- Recovery: Stop pulling against the unstable pile and have a person restack the displaced wooden blocks and restore the protruding target. Then realign the gripper and pull along the target block's extraction direction while monitoring neighboring blocks.
- Severity: low
- Severity evidence: Wooden blocks are displaced and topple onto the tabletop (frames 68–84, front, wrist), but no breakage or meaningful damage risk is visible.
- Resetability: minor_reset
- Resetability evidence: The blocks remain accessible on the tabletop; a straightforward manual restacking and target repositioning should restore a valid attempt state.