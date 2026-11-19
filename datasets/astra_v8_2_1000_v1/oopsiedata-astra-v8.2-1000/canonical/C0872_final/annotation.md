# Episode: C0872

## Episode annotation

- Language task: pick up the corn
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the corn remains on the tabletop throughout frames 0–49, while the gripper repeatedly opens and closes over the separate bowl behind it (for example, frames 2–10, 29–36 and 43–49). The robot never visibly approaches or lifts the corn; this is sustained non-task-directed behavior, not merely an unconfirmed lift at recording end.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 50 | Yes |

## Failure annotations

### Failure 1

- Frames: 0-50
- Categories: task_not_attempted
- Explanation: In right_shoulder_cam, the gripper stays over the bowl and repeatedly cycles its fingers throughout frames 0–49, rather than moving toward the clearly separate corn on the table. This continuous unproductive behavior makes no visible progress toward picking up the corn. The images do not establish possession of a bowl object or a mechanical malfunction.
- Recovery: Stop cycling the gripper, move clear of the bowl, align the open fingers around the corn, then close and lift while checking retention; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The corn remains undisturbed and no damage, spill or other meaningful harmful consequence is visible in right_shoulder_cam through frame 49.
- Resetability: immediate
- Resetability evidence: The corn remains accessible in its original tabletop position, so another task-directed attempt requires no visible environmental reset or human intervention.