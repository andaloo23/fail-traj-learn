# Episode: C0042

## Episode annotation

- Language task: Pick up the green cup and stack it on the purple.
- Success label: failure
- Outcome evidence: The cups begin separate in top frame 0. Repeated acquisition attempts leave the green cup on the table while the gripper withdraws empty (top and right_wrist frames 300–313, 505–517, and 702–723). At frame 749, top and right_wrist still show separate green and purple cups, with no completed stack. This is visibly unsuccessful acquisition, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 279 | No |
| 279 | 313 | Yes |
| 313 | 477 | No |
| 477 | 517 | Yes |
| 517 | 675 | No |
| 675 | 723 | Yes |
| 723 | 750 | No |

## Failure annotations

### Failure 1

- Frames: 279-313
- Categories: grasp
- Explanation: After closing near the green cup, the gripper moves away without acquiring it; right_wrist frames 279–306 show the cup separating from the fingers, and top frames 297–310 confirm it remains on the table. The withdrawal does not transport the cup toward a stack. Repositioning begins at frame 313.
- Recovery: Reopen the gripper, realign opposing fingers around the green cup, and verify retention with a small lift before transport; no human intervention is evidently needed.
- Severity: low
- Severity evidence: The cup remains upright on the table, with no visible damage or consequential disturbance in top frames 300–313.
- Resetability: immediate
- Resetability evidence: Both cups remain accessible and usable; another grasp can be attempted without environmental resetting.

### Failure 2

- Frames: 477-517
- Categories: grasp
- Explanation: A further closure near the green cup is followed by another empty withdrawal, visible in right_wrist frames 477–511. Top frames 501–516 show the green cup still on the table apart from the purple cup; no pickup is accomplished. Reapproach begins at frame 517.
- Recovery: Reassess the cup-to-finger alignment and grasp height rather than repeat the same acquisition geometry, then test retention before moving toward the purple cup; no human intervention is evidently needed.
- Severity: low
- Severity evidence: The failed acquisition delays the task but leaves both cups upright, with no visible damage in top frames 505–517.
- Resetability: immediate
- Resetability evidence: The missed grasp does not create an environmental state requiring intervention; the green cup remains available for retry.

### Failure 3

- Frames: 675-723
- Categories: grasp
- Explanation: Following another closure, the gripper again retreats without the green cup (right_wrist frames 675–715). Top frames 691–722 show the cup left behind on the table, so this attempt also fails to acquire the object needed for stacking. Repositioning resumes at frame 723.
- Recovery: Reopen and correct the grasp position using the visible cup boundaries, acquire the cup, and confirm a secure small lift before stacking; no human intervention is evidently needed.
- Severity: low
- Severity evidence: No drop from height, damage, or toppling is visible; the cups remain separate and upright in top frames 702–723.
- Resetability: immediate
- Resetability evidence: The scene remains valid for another acquisition attempt without moving or repairing objects.