# Episode: C0789

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the box.
- Success label: success but suboptimal
- Outcome evidence: External and wrist views show the animal acquired and lifted at frames 615–786, transferred toward the box at frames 865–1049, and released into it by frame 1065. The empty gripper withdraws at frames 1140–1155, and the animal remains supported in the box through frame 1571, with parts protruding over the rim. Sustained stationary intervals repeatedly interrupt acquisition and transfer; no failed grasp, damage, or unrelated side effect is established. Some pause onsets are approximate because the reconciliation images are selected checks rather than every source frame.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 233 | Yes |
| 233 | 255 | No |
| 255 | 312 | Yes |
| 312 | 330 | No |
| 330 | 408 | Yes |
| 408 | 425 | No |
| 425 | 508 | Yes |
| 508 | 525 | No |
| 525 | 593 | Yes |
| 593 | 616 | No |
| 616 | 675 | Yes |
| 675 | 698 | No |
| 698 | 769 | Yes |
| 769 | 787 | No |
| 787 | 865 | Yes |
| 865 | 883 | No |
| 883 | 959 | Yes |
| 959 | 978 | No |
| 978 | 1044 | Yes |
| 1044 | 1572 | No |

## Failure annotations

### Failure 1

- Frames: 0-233
- Categories: task_not_attempted
- Explanation: External and wrist frames 0–232 show essentially unchanged robot and object poses for about 15.5 seconds, with the gripper separated from the animal and no task progress. Approach begins at frame 233; the cause of inactivity is not visible.
- Recovery: Begin controlled alignment and approach to the animal; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The consequence is delay, without visible damage, object displacement, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The animal and box remain accessible and undisturbed; no environmental reset is needed.

### Failure 2

- Frames: 255-312
- Categories: task_not_attempted
- Explanation: Following initial movement, external and wrist checks at frames 255, 270, 285, and 300 show the same stationary gripper pose, interrupting approach for several seconds. Movement resumes around frame 312, as summarized in the preceding window and visible by frame 315. Frame 255 is the earliest supplied check establishing this stationary pose; the exact onset between the preceding movement and that check is uncertain.
- Recovery: Continue the controlled approach toward a graspable portion of the animal; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only delayed progress is established; the scene remains undisturbed.
- Resetability: immediate
- Resetability evidence: Neither the animal nor the box requires resetting before continuation.

### Failure 3

- Frames: 330-408
- Categories: task_not_attempted
- Explanation: External and wrist frames 330, 345, 350, 390, and 407 show the gripper stationary above the animal without acquisition progress. This pause crosses the window boundary rather than beginning at frame 350. Approach resumes at frame 408; its precise onset near the end of the preceding movement is uncertain, so frame 330 is the first stationary visual check used.
- Recovery: Resume alignment and descent while maintaining clearance from the table; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The pause delays acquisition without visible damage or harmful contact.
- Resetability: immediate
- Resetability evidence: The target remains on the table in an accessible state, requiring no reset.

### Failure 4

- Frames: 425-508
- Categories: task_not_attempted
- Explanation: External and wrist frames 425–507 show a sustained unchanged pose near the animal for about 5.5 seconds, without further alignment, closure, or lifting. Task-directed movement resumes at frame 508.
- Recovery: Continue careful descent and align the fingers for acquisition; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only delay is visible; no damage or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The animal and box remain suitable for continuing without environmental intervention.

### Failure 5

- Frames: 525-593
- Categories: task_not_attempted
- Explanation: External and wrist frames 525–592 show the open fingers remaining close to the animal for about 4.5 seconds without acquisition progress. Motion resumes at frame 593; proximity alone does not establish a failed grasp.
- Recovery: Complete alignment, close around a secure portion of the animal, and verify retention with a small lift; no human intervention is visibly needed.
- Severity: low
- Severity evidence: No damage, dropping, or disturbance is visible; the consequence is delayed acquisition.
- Resetability: immediate
- Resetability evidence: The scene requires no reset before the robot continues.

### Failure 6

- Frames: 616-675
- Categories: task_not_attempted
- Explanation: After closure and animal movement at frames 614–615, external and wrist frames 616–674 show the robot and animal stationary for about 3.9 seconds without lifting or transfer progress. Movement resumes at frame 675, followed by a lift; failed retention is not established.
- Recovery: Verify the hold and lift the animal clear of the table before transferring it toward the box; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The interval delays progress without visible damage or harmful side effects.
- Resetability: immediate
- Resetability evidence: The animal remains at the gripper and the box is undisturbed; no environmental reset is needed.

### Failure 7

- Frames: 698-769
- Categories: task_not_attempted
- Explanation: External and wrist frames 698–768 show the animal and gripper stationary near the table, interrupting the lift for about 4.7 seconds. The same pause extends across frame 700; lifting resumes at frame 769. Frame 698 is the earliest stationary seam check used, with the exact onset after the preceding lift uncertain.
- Recovery: Maintain retention and continue lifting clear of the table toward the box; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only delayed progress is established; no slipping, damage, or environmental disturbance is visible.
- Resetability: immediate
- Resetability evidence: The animal remains retained and the environment needs no resetting.

### Failure 8

- Frames: 787-865
- Categories: task_not_attempted
- Explanation: External and wrist frames 787–864 show the animal held stationary outside the box for about 5.2 seconds, without transfer progress. Movement toward the box resumes at frame 865.
- Recovery: Continue a controlled transfer while maintaining the grasp and clearance; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is delay, with no dropped object, damage, or meaningful damage risk established.
- Resetability: immediate
- Resetability evidence: The animal remains held and the box remains available, requiring no environmental intervention.

### Failure 9

- Frames: 883-959
- Categories: task_not_attempted
- Explanation: External and wrist frames 883–958 show the animal held near and above the box in an unchanged pose for about 5.1 seconds, without further positioning or release. Alignment resumes at frame 959; this is stalled progress, not a demonstrated failed placement.
- Recovery: Align the animal over the opening and lower it for release into the box; no human intervention is visibly required.
- Severity: low
- Severity evidence: No damage or disruption is visible; placement is merely delayed.
- Resetability: immediate
- Resetability evidence: The held animal and undisturbed box remain suitable for completing the task without resetting.

### Failure 10

- Frames: 978-1044
- Categories: task_not_attempted
- Explanation: External and wrist frames 978–1043 show the gripper and animal essentially stationary at the box for about 4.4 seconds without release progress. Movement resumes at frame 1044 and subsequently leads to successful placement; no hidden mechanical or planning cause is established.
- Recovery: Complete controlled positioning, release the animal into the box, and verify support before withdrawing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The interval delays completion without visible damage, dropping outside the box, or harmful side effects.
- Resetability: immediate
- Resetability evidence: The animal remains held and the box remains usable; continuation requires no environmental reset.