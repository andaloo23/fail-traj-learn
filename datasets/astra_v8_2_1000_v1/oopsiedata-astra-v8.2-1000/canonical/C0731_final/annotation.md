# Episode: C0731

## Episode annotation

- Language task: Pick green block and place on cardboard.
- Success label: failure
- Outcome evidence: In exterior_cam, the robot lifts the green block and carries it away from its initial position (frames 68–110), but drops it onto the foreground tabletop rather than the cardboard (frames 137–140). It later reacquires the block, visibly holding it in frames 518–599. At frame 599 it has not placed the block on the cardboard. The first transfer visibly fails; completion after the later acquisition remains unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 137 | No |
| 137 | 140 | Yes |
| 140 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 137-140
- Categories: grasp
- Explanation: In exterior_cam, the previously held green block separates from the gripper in frames 137–138 and falls toward the foreground tabletop, appearing at the bottom of the image in frame 139. This loses possession before placement; the cardboard remains farther back on the table. The images do not establish whether release or slipping caused the drop.
- Recovery: Locate the block on the tabletop, approach and regrasp it securely, then transport it over the cardboard and lower it before releasing. Human intervention is not evidently needed; verify its location and reachability before retrying.
- Severity: low
- Severity evidence: The block falls onto the otherwise clear tabletop; no damage or impact with unrelated objects is visible in exterior_cam frames 138–140.
- Resetability: immediate
- Resetability evidence: The displaced block can be reacquired without restoring other scene components, and later frames 518–599 show it held again without visible human resetting.