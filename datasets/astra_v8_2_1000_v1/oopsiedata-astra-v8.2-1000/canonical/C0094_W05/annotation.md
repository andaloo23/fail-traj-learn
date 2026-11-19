# Episode: C0094_W05

## Episode annotation

- Language task: pick up cup with one arm, hand over to the other arm, and place it on saucer
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this provisional window. In aria and right_wrist at frames 1400, 1575, and 1749, the right gripper stays at the cup near the saucer without discernible placement, release, or withdrawal; aria and left_wrist show the other gripper remaining open and away. The roughly 11.6 seconds of unchanged configuration establish sustained stalling, not a visibly failed grasp or drop. Earlier pickup and handover and the later outcome are not visible in the supplied window.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1750 | Yes |

## Failure annotations

### Failure 1

- Frames: 1400-1750
- Categories: task_not_attempted
- Explanation: Across frames 1400–1749, aria and right_wrist show essentially unchanged cup and right-gripper positions near the saucer, while left_wrist shows no useful movement of the open other gripper. This sustained inactivity does not advance the task. Context frames 1398–1399 show the same configuration, supporting continuity across the window boundary, but the stall's earlier onset is not established here and it may continue beyond frame 1749. No hidden mechanical or planning cause is established.
- Recovery: Reassess cup possession, alignment, and support, then complete any necessary lowering onto the saucer and release only when supported before withdrawing; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is delayed progress; no spill, drop, damage, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: No environmental disturbance requiring resetting is visible; task-directed action can resume from the current configuration without human resetting.