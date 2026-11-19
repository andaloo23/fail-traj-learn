# Episode: C0402

## Episode annotation

- Language task: Pick up the red bowl and place it in the grey bowl.
- Success label: success but suboptimal
- Outcome evidence: The first acquisition fails: frames 57–65 in right and wrist show the gripper withdrawing empty while the red bowl remains on the table. A later attempt lifts and transports the red bowl at frames 197–217. At frame 241, wrist shows the released red bowl nested inside the grey bowl; right confirms the gripper withdraws while both bowls remain together at frames 257–301. This completed state persists through frame 599 in both cameras.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 57 | No |
| 57 | 67 | Yes |
| 67 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 57-67
- Categories: grasp
- Explanation: Following the closing attempt at frames 41–56, the gripper rises away without the red bowl during frames 57–66 in right; wrist shows increasing separation between the closed fingers and the bowl. The bowl remains on the table rather than being acquired. At frame 67 the robot begins returning toward the bowl, subsequently reopening and realigning.
- Recovery: Reopen the fingers, align them across the red bowl’s rim, close securely, and verify that the bowl follows a small test lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The failed acquisition delays the task, but the bowl remains upright on the tabletop and neither camera shows damage or a meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The red bowl remains accessible on the table, so the robot can reattempt acquisition without environmental resetting or human assistance.