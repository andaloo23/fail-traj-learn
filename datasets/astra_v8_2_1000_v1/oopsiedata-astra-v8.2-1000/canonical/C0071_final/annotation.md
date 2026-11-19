# Episode: C0071

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image, the green can is placed in the upper blue tray by frame 1000, and both cans remain there by frame 2000. The robot engages and repositions the blue bowl but withdraws without it at frames 2782–3000. At frame 4009, both bowls remain on the tabletop and the right red tray is empty. Thus the task is visibly incomplete, with an unsuccessful bowl acquisition/retention attempt rather than merely an unconfirmed final placement. No later completion or abnormal interruption is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 2782 | No |
| 2782 | 3100 | Yes |
| 3100 | 4010 | Yes |

## Failure annotations

### Failure 1

- Frames: 2782-3100
- Categories: grasp
- Explanation: In base_image, the blue bowl changes position during engagement at frames 2200–2700, but the gripper withdraws empty at frames 2782–3000 while the bowl remains beside the upper tray instead of being transported to the right tray. This establishes failed acquisition or retention; occlusion prevents distinguishing the precise release mechanism or an earlier loss of purchase. Frame 2782 is the supported withdrawal boundary, not a claim of an exactly timed slip. The withdrawal continues across frame 2800 without a visible retry.
- Recovery: Reapproach the blue bowl, align around an accessible rim, and verify secure retention with a controlled lift before transporting it to the right tray; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The bowl remains upright and accessible on the table, with no visible damage, spill, or harmful displacement in base_image frames 2799–3100.
- Resetability: immediate
- Resetability evidence: The bowl and empty destination tray remain accessible; no environmental reset is required before another grasp attempt.

### Failure 2

- Frames: 3100-4010
- Categories: task_not_attempted
- Explanation: After withdrawing, the robot remains near the upper image edge without discernible task progress in base_image frames 3100, 3150, 3500, 3850, and 4009. Both bowls remain outside the empty right tray throughout this approximately nine-second interval. This is one continuous sustained stall, including the final window, rather than separate failures at window boundaries. Frame 3100 is the earliest selected check supporting the settled stalled state; the exact onset between checks is uncertain. The recording ending does not establish abnormal termination.
- Recovery: Resume bowl acquisition, verify a secure grasp, and place each bowl in the right tray; no physical human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is lack of task progress; base_image frames 3100–4009 show no damage or supported risk of damage.
- Resetability: immediate
- Resetability evidence: Both bowls remain upright on the tabletop and the destination tray remains empty, so the environment needs no physical reset before execution resumes.