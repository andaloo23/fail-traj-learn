# Episode: C0066

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the box.
- Success label: failure
- Outcome evidence: The stuffed animal starts on the table beside the empty box (frame 0, external and wrist). The robot approaches and operates its gripper, but the animal remains on the table after the attempted lift (frames 845–858, external and wrist). At frame 1072, external still shows the animal outside the box, while wrist shows the open gripper near its head; no completed pickup or placement is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 149 | Yes |
| 149 | 850 | No |
| 850 | 920 | Yes |
| 920 | 1073 | No |

## Failure annotations

### Failure 1

- Frames: 0-149
- Categories: task_not_attempted
- Explanation: The arm and open gripper remain stationary for approximately ten seconds, without approaching or acquiring the animal (frames 0, 75 and 148, external and wrist). This sustained initial inactivity makes no visible task progress; movement begins at frame 149.
- Recovery: Begin a controlled approach and align the open fingers around a graspable portion of the animal; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Only progress is delayed; neither camera shows damage or disturbance to the scene during this interval.
- Resetability: immediate
- Resetability evidence: The animal and box remain in their initial usable positions, so no environmental reset is needed.

### Failure 2

- Frames: 850-920
- Categories: grasp
- Explanation: Following finger closure near the animal at frames 845–849, the gripper rises away without lifting it at frames 850–858; external shows the animal remaining on the table and wrist shows separation from the closed fingers. The robot then holds this unsuccessful position through frame 919 rather than transporting the animal.
- Recovery: Reopen the gripper, realign around a substantial portion of the animal, close securely, and verify retention with a small controlled lift before moving toward the box; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The failed acquisition leaves the soft animal on the tabletop, with no visible damage, spill, or harmful collision.
- Resetability: immediate
- Resetability evidence: The animal remains accessible on the table and the box remains usable; another grasp can be attempted without scene resetting.