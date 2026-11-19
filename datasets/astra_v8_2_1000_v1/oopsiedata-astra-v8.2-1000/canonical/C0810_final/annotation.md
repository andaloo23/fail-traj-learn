# Episode: C0810

## Episode annotation

- Language task: stack the blue block on the yellow block
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the blue block in frames 21–32 and lowers it toward the yellow block in frames 43–47. The blue block tips away at frame 48 and lands separately on the table in frames 49–50, visibly failing the placement. Frames 53–69 show a renewed acquisition attempt, but no completed stack is visible before the episode ends.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 48 | No |
| 48 | 51 | Yes |
| 51 | 70 | No |

## Failure annotations

### Failure 1

- Frames: 48-51
- Categories: manipulation
- Explanation: In right_shoulder_cam, the previously held blue block tips left during placement at frame 48, falls away from the yellow block at frame 49, and rests separately on the table at frame 50. The placement fails to establish a supported stack; the images do not establish a hidden mechanical or planning cause.
- Recovery: Reacquire the blue block, align its base securely over the yellow block, lower it into stable contact, and release before withdrawing. No human intervention appears necessary.
- Severity: low
- Severity evidence: The blue block falls a short distance onto the tabletop and remains intact and accessible; no damage or disruption to unrelated objects is visible in right_shoulder_cam frames 49–51.
- Resetability: immediate
- Resetability evidence: Both blocks remain upright and accessible on the table, so the robot can immediately attempt another pickup and placement without environmental resetting or human intervention.