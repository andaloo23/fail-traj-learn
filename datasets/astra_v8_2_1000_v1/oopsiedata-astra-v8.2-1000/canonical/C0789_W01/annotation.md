# Episode: C0789_W01

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the box.
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window: external and wrist frames 0, 232, and 349 show the stuffed animal remaining on the table outside the box. After prolonged initial inactivity, the gripper begins approaching the animal (frames 233–245 and 312–328), but no completed acquisition or placement is visible. This is a provisional window outcome, not evidence of a failed grasp or final whole-episode failure; later context is absent.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 233 | Yes |
| 233 | 350 | No |

## Failure annotations

### Failure 1

- Frames: 0-233
- Categories: task_not_attempted
- Explanation: In external and wrist frames 0–232, the robot maintains essentially the same pose with the empty gripper separated from the stuffed animal, while the animal and box remain stationary. This roughly 15.5-second interval shows sustained inactivity rather than an approach or acquisition. Task-directed movement becomes visible at frame 233; the reason for the preceding inactivity is not visible.
- Recovery: Begin a controlled approach, align the open fingers around the stuffed animal, acquire and verify a secure hold, then lift and transfer it into the box; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is delayed task progress; external and wrist frames 0–232 show no displaced objects, damage, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The animal remains accessible on the table and the box remains undisturbed, so another attempt requires no environmental reset or human intervention.