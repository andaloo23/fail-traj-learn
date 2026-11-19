# Episode: C0789_W02

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the box.
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this observed window, rather than a visibly failed grasp: external and wrist frames 350–699 show incremental approach, closing around the animal near frames 605–615, and upward movement with the animal at frames 680–692, but no placement in the box. Several sustained stationary intervals interrupt progress. Later context is absent, so this is a provisional window outcome, not a final whole-episode failure.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 408 | Yes |
| 408 | 425 | No |
| 425 | 508 | Yes |
| 508 | 525 | No |
| 525 | 593 | Yes |
| 593 | 616 | No |
| 616 | 675 | Yes |
| 675 | 700 | No |

## Failure annotations

### Failure 1

- Frames: 350-408
- Categories: task_not_attempted
- Explanation: External and wrist frames 350–407 show the gripper stationary above and separated from the animal for approximately 3.9 seconds, without acquisition progress; approach resumes at frame 408. Context frames 348–349 show the same pose, so the pause may begin before this window; its earlier extent cannot be established from the supplied images, regardless of the prior No label.
- Recovery: Resume controlled alignment and descent toward a secure grasp; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Only delayed progress is visible; the animal, box, and surroundings remain undisturbed in external and wrist frames 350–407.
- Resetability: immediate
- Resetability evidence: The target remains accessible and no environmental reset is required.

### Failure 2

- Frames: 425-508
- Categories: task_not_attempted
- Explanation: Following the approach, external and wrist frames 425–507 show an unchanged gripper pose near the animal for approximately 5.5 seconds, with no closing, lifting, or further alignment visible. Task-directed descent resumes at frame 508; the reason for the stationary interval is not visible.
- Recovery: Continue careful descent and align the fingers around the animal before closing; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is delay, with no damage or meaningful damage risk established in external and wrist frames 425–507.
- Resetability: immediate
- Resetability evidence: Neither the animal nor the box needs resetting before the robot continues.

### Failure 3

- Frames: 525-593
- Categories: task_not_attempted
- Explanation: External and wrist frames 525–592 show another sustained stationary interval of approximately 4.5 seconds with the open fingers close to the animal, but no visible acquisition progress. Movement toward the animal resumes at frame 593; proximity alone does not establish a failed grasp.
- Recovery: Complete alignment and close the fingers around a secure portion of the animal, then verify retention with a small lift; no human intervention is visibly needed.
- Severity: low
- Severity evidence: No damage, dropped object, or disrupted surroundings are visible; this interval delays acquisition.
- Resetability: immediate
- Resetability evidence: The scene remains suitable for continuing the acquisition without an environmental reset.

### Failure 4

- Frames: 616-675
- Categories: task_not_attempted
- Explanation: After the fingers close and the animal shifts at external and wrist frames 605–615, frames 616–674 show the robot and animal stationary for approximately 3.9 seconds, without lifting or transfer progress. Movement resumes at frame 675 and subsequent frames show the animal rising with the gripper; the pause does not establish failed retention.
- Recovery: Verify a secure hold, lift clear of the table, and transfer the animal into the box; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only stalled progress is established; external and wrist frames 616–674 show no visible damage or harmful side effect.
- Resetability: immediate
- Resetability evidence: The animal remains accessible at the gripper and the box is undisturbed, so no environmental reset is needed.