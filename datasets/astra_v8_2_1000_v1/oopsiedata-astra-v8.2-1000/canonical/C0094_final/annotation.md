# Episode: C0094

## Episode annotation

- Language task: pick up cup with one arm, hand over to the other arm, and place it on saucer
- Success label: failure
- Outcome evidence: aria and left_wrist show the cup lifted at frames 510–600; aria, left_wrist, and right_wrist show transfer to the right gripper at frames 690–720 as the left gripper opens and withdraws. The right arm brings the cup toward the saucer at frames 750–1110. However, aria and right_wrist show the gripper remaining around the cup through frame 5145, without a confirmed release or independently supported placement. Completion is unconfirmed rather than a demonstrated drop or failed grasp; prolonged inactivity before completing placement is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1110 | No |
| 1110 | 5146 | Yes |

## Failure annotations

### Failure 1

- Frames: 1110-5146
- Categories: task_not_attempted
- Explanation: Following small positioning changes visible through approximately frame 1110, aria and right_wrist show essentially unchanged cup and right-gripper positions near the saucer at frames 1140, 1400, 2100, 3150, 4200, and 5145; left_wrist shows the other gripper open and away. This continuous inactivity lasts approximately 134 seconds without a visible release or further placement progress. The onset is approximate at the supplied checks' temporal resolution, rather than tied to a window boundary. No mechanical cause or abnormal termination is established.
- Recovery: Reassess the cup's alignment and support, complete any necessary lowering onto the saucer, and release and withdraw only after confirming stable support; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is incomplete task execution and prolonged delay; no drop, spill, damage, or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The cup and saucer remain accessible without visible environmental disturbance, so placement can resume without a human reset.