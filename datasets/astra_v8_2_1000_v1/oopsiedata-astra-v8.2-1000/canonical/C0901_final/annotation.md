# Episode: C0901

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The first acquisition fails: the gripper withdraws empty while the spoon remains on the table (frames 44–64, image, left_ego_image and wrist_image). A second attempt lifts the spoon (frames 136–166, left_ego_image and wrist_image) and carries it toward the drawer. However, the robot then holds it nearly stationary without releasing it through frame 399 (frames 250–399, image and wrist_image). Placement is not completed visibly; the final spoon remains held rather than confirmed deposited.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 34 | No |
| 34 | 78 | Yes |
| 78 | 250 | No |
| 250 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 34-78
- Categories: grasp
- Explanation: The fingers close beside the spoon without acquiring it (frames 34–42, wrist_image). The subsequent upward withdrawal leaves the spoon on the tabletop and the gripper empty (frames 44–64, image and left_ego_image), establishing a failed acquisition. The segment ends when the fingers reopen for another approach at frame 78.
- Recovery: Reopen the gripper, align the fingers on opposite sides of the spoon, and verify a secure acquisition with a small lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon remains accessible on the table, with no visible damage or harmful disturbance to other objects.
- Resetability: immediate
- Resetability evidence: No environmental reset is required; the robot can realign and retry the grasp directly.

### Failure 2

- Frames: 250-400
- Categories: task_not_attempted
- Explanation: After acquiring and transporting the spoon, the robot sustains a nearly unchanged holding pose for the remaining approximately 12.5 seconds (frames 250, 300, 350 and 399, image and wrist_image). The spoon stays between the fingers, with no discernible insertion or release advancing the unfinished placement.
- Recovery: Reassess the spoon and drawer opening, then resume a clearance-checked placement and release only when the spoon is supported inside the drawer; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is an unfinished task; the spoon remains held, and no damage, dropping or harmful collision is visible.
- Resetability: immediate
- Resetability evidence: The environment remains usable and the spoon is already acquired, so placement can resume without a physical scene reset.