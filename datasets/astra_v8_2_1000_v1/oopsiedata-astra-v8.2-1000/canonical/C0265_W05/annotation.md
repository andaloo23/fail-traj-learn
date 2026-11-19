# Episode: C0265_W05

## Episode annotation

- Language task: find the cube under the green bowl
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window: the green bowl remains inverted and no cube is uncovered (left and top, frames 1400, 1500, 1600 and 1749). The robot makes only small positional changes without contacting or lifting the bowl; right also shows no object acquisition. This window establishes sustained lack of progress, not a visibly failed grasp. The outcome is provisional because earlier execution beyond the supplied context frames and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1750 | Yes |

## Failure annotations

### Failure 1

- Frames: 1400-1750
- Categories: task_not_attempted
- Explanation: Across approximately 11.6 seconds, the grippers remain apart from the inverted bowl with only small positional changes and no discernible attempt to uncover it (left, right and top, frames 1400, 1500, 1600, 1700 and 1749). The prolonged inactivity does not advance finding the cube. Unlike the preceding report's interpretation of preparation, the supplied window provides sustained evidence of stalling; its continuity before frame 1400 is unresolved, and it may continue after frame 1749.
- Recovery: Approach the green bowl, align the gripper for a secure grasp, lift it clear of the table and inspect underneath for the cube; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Only progress is prevented; the bowl and surrounding scene remain unchanged, with no visible damage or supported damage risk.
- Resetability: immediate
- Resetability evidence: No objects have been displaced or damaged, so the robot can resume a task-directed attempt without an environmental reset.