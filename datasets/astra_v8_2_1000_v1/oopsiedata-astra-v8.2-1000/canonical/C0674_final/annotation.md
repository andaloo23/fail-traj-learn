# Episode: C0674

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the box.
- Success label: failure
- Outcome evidence: In external and wrist, the stuffed animal remains on the table outside the box from frame 0 through frame 1273. The robot approaches and changes its alignment around the animal (frames 153–633), but no successful acquisition, lift, or placement is visible. It subsequently remains near the animal with only small adjustments and no task progress. This is an observed incomplete task with sustained stalling, not evidence of a dropped object or abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 153 | Yes |
| 153 | 634 | No |
| 634 | 1274 | Yes |

## Failure annotations

### Failure 1

- Frames: 0-153
- Categories: task_not_attempted
- Explanation: In external and wrist, frames 0–152 show the gripper and scene remaining unchanged for approximately ten seconds, without an approach or acquisition attempt. Task-directed movement begins at frame 153.
- Recovery: Begin a controlled approach, align the open gripper around a graspable part of the animal, and acquire it; no human intervention is visibly required.
- Severity: low
- Severity evidence: The delay prevents progress but causes no visible object displacement, damage, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The animal and box remain in their original usable positions; no environmental reset is needed.

### Failure 2

- Frames: 634-1274
- Categories: task_not_attempted
- Explanation: Following the preceding approach and alignment, external and wrist show sustained hovering near the animal from frame 634 onward, with minor adjustments but no acquisition or transport. Frames 800, 1000, 1114, and 1273 confirm that the animal remains on the table and the box remains empty; the prolonged interval does not advance the task.
- Recovery: Reassess the gripper’s position relative to the animal, align the jaws around its torso or another secure grasp region, close, and verify retention with a small lift before moving to the box. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The task remains unfinished, but no damage, drop, or harmful collision is visible.
- Resetability: immediate
- Resetability evidence: The animal remains accessible on the table and the box remains usable; another acquisition attempt requires no scene reset.