# Episode: C0692

## Episode annotation

- Language task: pick up cup with one arm, hand over to the other arm, and place it on saucer
- Success label: failure
- Outcome evidence: The robot approaches the cup but does not visibly complete pickup, handover, or placement. In aria and left_wrist, frames 120-170 show approach toward the cup, followed by prolonged near-stationary hovering. Later frames 470-676 show further positioning near the cup, without confirmed acquisition; aria and right_wrist show the saucer remaining empty through frame 676. Completion is unconfirmed, rather than a demonstrated completed grasp followed by loss or empty withdrawal.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 175 | No |
| 175 | 363 | Yes |
| 363 | 677 | No |

## Failure annotations

### Failure 1

- Frames: 175-363
- Categories: task_not_attempted
- Explanation: After approaching the cup, the robot remains nearly stationary with its gripper open beside it for approximately six seconds. aria and left_wrist at frames 175, 240, 300 and 360 show no meaningful acquisition progress or cup movement; right_wrist shows no handover preparation beyond the existing pose. Small positional drift does not resolve this sustained stall. Renewed positioning is visible after frame 363.
- Recovery: Resume task-directed alignment, close the gripper securely around the cup, and verify a controlled lift before preparing the other arm for handover; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is lost progress; the cup and saucer remain upright, with no observed damage, spill or harmful collision.
- Resetability: immediate
- Resetability evidence: The stall leaves the objects in a usable state on the table, so another acquisition attempt requires no environmental reset or human intervention.