# Episode: C0871

## Episode annotation

- Language task: Stack the green cup into the purple cup.
- Success label: failure
- Outcome evidence: In exterior_cam, the robot lifts the green cup and carries it toward the purple cup (frames 73–117), but does not establish a stable stack. The cups tip apart during placement (frames 161–175). The green cup subsequently rolls toward the left table edge and falls out of view (frames 217–224); the purple cup remains separate at frame 240. This is a visibly failed attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 161 | No |
| 161 | 176 | Yes |
| 176 | 217 | No |
| 217 | 225 | Yes |
| 225 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 161-176
- Categories: manipulation, grasp
- Explanation: In exterior_cam, the previously held green cup tilts away from its placement alignment with the purple cup beginning around frame 161. By frames 169–175, the green cup has fallen onto its side on the tabletop and the purple cup is also tipped, rather than forming a stable nested stack. Acquisition was established earlier, but placement and retention fail; the precise contact mechanics are obscured by the gripper.
- Recovery: Reacquire and upright the cups, stabilize the purple cup, then align the green cup vertically over its opening and lower it before releasing. Human intervention is not necessarily needed if the robot can safely handle the sideways cups.
- Severity: low
- Severity evidence: Both cups topple on the tabletop without visible breakage, spilled contents, or damage in exterior_cam frames 169–175.
- Resetability: minor_reset
- Resetability evidence: The cups need straightforward repositioning and uprighting before another stacking attempt; both remain accessible on the table at the end of this segment.

### Failure 2

- Frames: 217-225
- Categories: grasp
- Explanation: After following the rolling green cup in exterior_cam frames 176–216, the gripper makes a near-object acquisition attempt at the left edge in frames 217–221 without securing it. The cup continues past the edge in frames 222–223 and disappears below it by frame 224 while the gripper remains empty. The images do not establish whether gripper contact accelerated its motion.
- Recovery: Stop the edge-side attempt and have a person locate, inspect, and return the fallen green cup to a safe tabletop position before retrying; do not reach blindly below the table.
- Severity: low
- Severity evidence: The visible consequence is loss of the cup off the tabletop and failure to acquire it. Its landing is unseen, so damage cannot be confirmed; no meaningful damage is visible.
- Resetability: minor_reset
- Resetability evidence: A person must retrieve and replace the green cup and upright the cups. This appears to be a straightforward reset, although the fallen cup's exact resting location and accessibility are not visible.