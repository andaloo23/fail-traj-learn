# Episode: C0772

## Episode annotation

- Language task: remove the blue cloth from the yellow block
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the gripper approaches and closes near the cloth at frames 0–16, then withdraws empty at frames 17–50 while the cloth remains in place. Frames 51–69 show no further attempt or cloth removal. This is a visibly failed acquisition, not merely unconfirmed completion. The yellow block is not visible, so its position beneath the cloth cannot be independently verified.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 17 | No |
| 17 | 51 | Yes |
| 51 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 17-51
- Categories: grasp
- Explanation: In right_shoulder_cam, after closing at frames 13–16, the gripper begins lifting away at frame 17 without lifting the cloth. It continues withdrawing empty through frame 50 while the cloth retains its original arrangement, establishing failed acquisition rather than successful removal.
- Recovery: Reopen the gripper, approach an accessible cloth edge or fold, and acquire it before lifting; verify that the cloth moves with the gripper before transporting it away. No human intervention is visibly required.
- Severity: low
- Severity evidence: The cloth remains on the table, with no visible damage, displaced unrelated objects, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The failed grasp leaves the scene essentially unchanged, allowing another acquisition attempt without environmental resetting.

### Failure 2

- Frames: 51-70
- Categories: task_not_attempted
- Explanation: In right_shoulder_cam, frames 51–69 show the empty gripper remaining withdrawn above and to the right of the unchanged cloth for approximately four seconds, with no renewed approach or other task progress after the failed grasp.
- Recovery: Resume a task-directed approach and retry acquisition of a visible cloth edge, checking possession before removal. No human intervention is visibly required.
- Severity: low
- Severity evidence: The inactivity prevents completion but causes no visible damage or additional scene disruption.
- Resetability: immediate
- Resetability evidence: The cloth remains available in the same location, and no cleanup or object repositioning is visibly needed before retrying.