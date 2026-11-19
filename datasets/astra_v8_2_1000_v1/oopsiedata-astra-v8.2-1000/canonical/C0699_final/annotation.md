# Episode: C0699

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The first pickup ends with the spoon falling back onto the table at frames 101–105 (wrist_image, left_ego_image). The robot reacquires and lifts it at frames 187–214, then moves toward the drawer. At frames 304–399, the spoon remains held outside the drawer with no visible placement (wrist_image, left_ego_image). Completion is unconfirmed, with an observed failed retention attempt and subsequent sustained lack of progress.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 101 | No |
| 101 | 109 | Yes |
| 109 | 304 | No |
| 304 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 101-109
- Categories: grasp
- Explanation: After lifting the spoon, the robot loses retention: the spoon separates from the fingers at frames 101–102 and falls flat onto the table by frames 103–105, while the gripper withdraws empty (wrist_image, left_ego_image). This undoes the pickup rather than advancing placement.
- Recovery: Reapproach the spoon, obtain a more secure grasp, and verify retention with a small lift before transport; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon lands on the tabletop without visible damage or disruption to nearby objects (frames 103–108, left_ego_image).
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the table and can be grasped again without environmental resetting.

### Failure 2

- Frames: 304-400
- Categories: task_not_attempted
- Explanation: The robot remains essentially stationary holding the spoon beside the drawer throughout frames 304–399, with no visible drawer opening, insertion, or release (image, left_ego_image, wrist_image). This sustained pause does not advance the unfinished task; the images do not establish its internal cause.
- Recovery: Resume task-directed motion, ensure the drawer is open sufficiently, and place and release the spoon inside; if necessary, safely set the spoon down first to free the gripper for opening the drawer. No human intervention is visibly required.
- Severity: low
- Severity evidence: The spoon remains held, with no visible damage, dropping, or harmful contact during the stationary interval.
- Resetability: immediate
- Resetability evidence: No environmental disruption needs resetting; the task can continue from the held-spoon state.