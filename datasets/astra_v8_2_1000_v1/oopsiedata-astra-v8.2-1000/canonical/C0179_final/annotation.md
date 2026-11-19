# Episode: C0179

## Episode annotation

- Language task: Pick up the spoon and place it in the sink.
- Success label: failure
- Outcome evidence: The spoon begins on the counter beside the sink (frame 0, right and wrist). Repeated acquisition attempts leave it on the counter as the gripper lifts away (frames 81, 145, and 265, right and wrist). At frame 299 it is still outside the sink; placement is visibly unachieved, not merely hidden or unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 75 | No |
| 75 | 84 | Yes |
| 84 | 137 | No |
| 137 | 148 | Yes |
| 148 | 217 | No |
| 217 | 267 | Yes |
| 267 | 300 | No |

## Failure annotations

### Failure 1

- Frames: 75-84
- Categories: grasp
- Explanation: After closing near the spoon, the gripper rises without retaining it (frames 75-81, right and wrist). By frame 81 the spoon bowl is visibly separate from the fingers and the spoon remains on the counter, establishing failed acquisition rather than successful pickup.
- Recovery: Reopen, align the fingers around a graspable section of the spoon, and verify retention with a small lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon remains on the counter with no visible damage or harmful side effect.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible for another grasp without environmental intervention.

### Failure 2

- Frames: 137-148
- Categories: grasp
- Explanation: Following another closure and attempted lift, the spoon separates from the fingers at frame 137 (wrist); the gripper continues upward empty while the spoon rests on the counter (frames 138-147, right and wrist). This attempt does not secure the spoon for transfer.
- Recovery: Reacquire the spoon using a better-centered grasp, then check that the entire utensil follows the gripper during a short lift; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon shifts on the counter but remains intact, with no visible damage to the surroundings.
- Resetability: immediate
- Resetability evidence: Its changed position still permits a direct autonomous retry; no manual reset is visibly required.

### Failure 3

- Frames: 217-267
- Categories: grasp
- Explanation: After closing again, the gripper makes repeated small lifting motions without lifting the spoon from the counter (frames 217-255, right and wrist). It subsequently opens and withdraws empty (frames 256-266), with clear separation visible at frame 265 in wrist and the spoon still on the counter in right.
- Recovery: Reposition the open fingers around the spoon handle or neck rather than repeating the ineffective contact, close securely, and verify pickup before moving toward the sink; no human intervention is needed.
- Severity: low
- Severity evidence: The unsuccessful acquisition costs time but causes no visible damage, spill, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The spoon and sink remain usable and accessible; another attempt requires only robot repositioning, not an environmental reset.