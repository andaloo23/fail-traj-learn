# Episode: C0351_W01

## Episode annotation

- Language task: pick up cup with one arm, hand over to the other arm, and place it on saucer
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window, not a visibly failed grasp: aria shows the cup and saucer remaining separate and unmoved from frame 0 through frame 349. left_wrist and right_wrist show empty, open grippers with modest initial repositioning but no acquisition or handover. The later stationary interval shows no task progress; subsequent episode context is unavailable, so this outcome is provisional.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 190 | No |
| 190 | 350 | Yes |

## Failure annotations

### Failure 1

- Frames: 190-350
- Categories: task_not_attempted
- Explanation: Following modest initial repositioning, the robot remains essentially stationary away from the cup for approximately 5.3 seconds. aria at frames 190, 240, 300 and 349 shows no approach to or displacement of either object; left_wrist and right_wrist show empty open grippers without acquisition activity. This sustained inactivity does not advance the task. Its cause is not visible, and it may continue beyond this window.
- Recovery: Resume a task-directed approach to the cup, align one gripper for acquisition, and verify a secure grasp before attempting the handover; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only lack of progress is observed; the cup and saucer remain undisturbed, with no visible damage or supported damage risk.
- Resetability: immediate
- Resetability evidence: The scene remains valid for an attempt, with both objects on the table and no environmental resetting or human intervention needed.