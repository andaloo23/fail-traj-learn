# Episode: C0094_W15

## Episode annotation

- Language task: pick up cup with one arm, hand over to the other arm, and place it on saucer
- Success label: failure
- Outcome evidence: Provisional for this window: frames 4900–5145 in aria, left_wrist, and right_wrist show an unchanged configuration, with one gripper beside the cup and saucer and the other open away from them. No pickup, handover, or release confirming completed placement is visible. Completion is unconfirmed, not a visibly failed grasp or placement; earlier task execution is unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 4900 | 5146 | Yes |

## Failure annotations

### Failure 1

- Frames: 4900-5146
- Categories: task_not_attempted
- Explanation: Throughout frames 4900–5145, including 5000 and 5100, aria and right_wrist show no discernible movement of the cup, saucer, or adjacent gripper; left_wrist shows the other gripper remaining open and stationary. This approximately 8.2-second inactivity makes no visible task progress. Context frames 4898–4899 show the same configuration, supporting continuity across the starting boundary independently of the prior prediction. The earlier onset and any continuation beyond this window are unknown; the window end does not establish abnormal termination.
- Recovery: Reassess cup possession and support, then resume whichever pickup, handover, or placement steps remain; verify stable support on the saucer before releasing and withdrawing. No human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is delayed progress; no drop, spill, damage, or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: No environmental disturbance requiring resetting is visible; the robot can resume task-directed action from the current configuration without a human reset.