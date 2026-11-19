# Episode: C0858

## Episode annotation

- Language task: put the corn on the green cloth
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot acquires the corn and carries it toward the green cloth (frames 20–52), then lowers it onto or near the cloth while retaining its grasp (frames 53–55). Instead of releasing it, the robot lifts and carries it toward and beyond the cloth’s right edge (frames 56–69). The corn remains in the gripper at frame 69; placement is not completed in the observed episode.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 62 | No |
| 62 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 62-70
- Categories: manipulation
- Explanation: After bringing the held corn over the cloth in frames 53–61, the robot carries it beyond the cloth’s right edge without releasing it in frames 62–69 of right_shoulder_cam. This visibly moves the acquired object away from the placement area rather than completing the requested placement; the preceding lifting and repositioning alone are not sufficient to establish failure.
- Recovery: Move the held corn back over the center of the cloth, lower it until supported, release it, and withdraw the gripper; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The corn remains held, and no damage, dropping, or disturbance of unrelated objects is visible in right_shoulder_cam through frame 69.
- Resetability: immediate
- Resetability evidence: The corn is still acquired and the cloth remains accessible and undisturbed, so placement can be reattempted without an environmental reset.