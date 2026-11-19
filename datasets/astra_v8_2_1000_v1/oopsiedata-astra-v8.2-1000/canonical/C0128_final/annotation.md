# Episode: C0128

## Episode annotation

- Language task: pick up cup with one arm, hand over to the other arm, and place it on saucer
- Success label: failure
- Outcome evidence: The cup is lifted by the right arm (frames 285–330, aria and right_wrist) and transferred to the left arm (frames 520–600, aria, left_wrist and right_wrist). After a prolonged pause, it is released onto the table beside rather than on the saucer (frames 1183–1240, aria and left_wrist). At frame 1299, aria shows the upright cup and saucer remaining separate, visibly establishing failed placement rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 830 | No |
| 830 | 1159 | Yes |
| 1159 | 1227 | Yes |
| 1227 | 1300 | No |

## Failure annotations

### Failure 1

- Frames: 830-1159
- Categories: task_not_attempted
- Explanation: The left arm holds the cup near the saucer with essentially unchanged object and gripper positions for approximately 11 seconds; frames 830, 950, 1050 and 1158 in aria and left_wrist show no meaningful progress toward placement during this sustained pause.
- Recovery: Resume task-directed motion by aligning the cup's base with the saucer center, lowering it onto the saucer and then releasing it; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The pause delays completion; no damage, drop or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The cup remains held and the saucer remains accessible, so work can resume without resetting the environment.

### Failure 2

- Frames: 1159-1227
- Categories: manipulation
- Explanation: The left gripper opens and withdraws while the cup is positioned away from the saucer; frames 1159–1190 in left_wrist show release, and frames 1205–1226 in aria show the cup left upright on the bare tabletop beyond the saucer instead of on it.
- Recovery: Reacquire the upright cup, align its base over the saucer, lower it until supported and release; no human intervention is needed based on the visible state.
- Severity: low
- Severity evidence: The cup is misplaced but stays upright on the table, with no visible breakage or spillage.
- Resetability: immediate
- Resetability evidence: Both cup and saucer remain accessible and intact; the robot can directly reattempt placement without human resetting.
