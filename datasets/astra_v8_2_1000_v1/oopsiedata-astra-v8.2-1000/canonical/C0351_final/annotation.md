# Episode: C0351

## Episode annotation

- Language task: pick up cup with one arm, hand over to the other arm, and place it on saucer
- Success label: failure
- Outcome evidence: aria at frames 0, 700, 930, 1400 and 1699 shows the cup remaining upright on the tabletop rather than being picked up or placed on the saucer. left_wrist and right_wrist show arm repositioning and empty grippers, with no visible cup transfer. Completion is unconfirmed, and sustained stalling is observed; no failed cup acquisition, dropping or abnormal termination is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 190 | No |
| 190 | 436 | Yes |
| 436 | 1050 | No |
| 1050 | 1700 | Yes |

## Failure annotations

### Failure 1

- Frames: 190-436
- Categories: task_not_attempted
- Explanation: After initial repositioning, the arms remain essentially stationary away from the cup for approximately 8.2 seconds. aria at frames 190, 300, 350 and 435 shows undisturbed objects, while left_wrist and right_wrist show empty open grippers without acquisition activity. This is one continuous stall across frame 350, ending as repositioning resumes around frame 436; its cause is not visible.
- Recovery: Resume a controlled cup-directed approach, align one gripper and verify secure acquisition before attempting the handover; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is delayed progress only; neither object is displaced or damaged, and no concrete damage risk is established.
- Resetability: immediate
- Resetability evidence: The cup and saucer remain in valid tabletop positions, permitting another attempt without environmental resetting or human intervention.

### Failure 2

- Frames: 1050-1700
- Categories: task_not_attempted
- Explanation: Following arm repositioning, both grippers hover without discernible cup-directed progress for approximately 21.7 seconds. aria at frames 1050, 1200, 1400, 1500 and 1699 shows the cup unchanged, while left_wrist and right_wrist show essentially unchanged empty gripper configurations with slight drift. The interval is a continuous stall, not separate failures at frame 1400. Its onset is approximate around frame 1050; the recording ending does not establish abnormal termination.
- Recovery: Reorient toward the cup, acquire it securely with one arm, verify retention during transfer to the other arm, and then place and release it on the saucer; no human intervention is visibly required.
- Severity: low
- Severity evidence: Progress is prevented, but no object displacement, damage or concrete risk of damage is visible.
- Resetability: immediate
- Resetability evidence: The cup remains upright and the environment remains usable for another attempt without a physical reset or human intervention.