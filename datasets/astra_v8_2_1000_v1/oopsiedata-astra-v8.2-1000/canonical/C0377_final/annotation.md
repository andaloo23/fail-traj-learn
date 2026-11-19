# Episode: C0377

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: success but side effects
- Outcome evidence: The spoon is successfully lifted on the second attempt (frames 208–240, image and left_ego_image), then released into the open drawer at frames 281–283; it remains visibly inside as the empty gripper withdraws (frames 284–307, image and wrist_image). Earlier, the gripper tips and shifts the unrelated yellow plate (frames 41–47, all three cameras), and the first spoon acquisition fails, followed by an empty trip to the drawer (frames 58–135).

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 41 | No |
| 41 | 48 | Yes |
| 48 | 58 | No |
| 58 | 136 | Yes |
| 136 | 308 | No |

## Failure annotations

### Failure 1

- Frames: 41-48
- Categories: collision
- Explanation: While approaching the spoon, the gripper contacts the unrelated yellow plate, visibly tipping it onto its edge and shifting it before it settles back down (frames 41–47, image, left_ego_image and wrist_image). This disturbs an object not required for the task.
- Recovery: Clear the plate before realigning over the spoon and use an approach that avoids its rim; no human intervention is needed for the visible state.
- Severity: low
- Severity evidence: The empty plate settles on the tabletop without visible breakage, spill or other damage.
- Resetability: immediate
- Resetability evidence: The plate remains stable on the table and the spoon remains accessible; another attempt requires no environmental intervention.

### Failure 2

- Frames: 58-136
- Categories: grasp, sequencing_semantic
- Explanation: Following the first closing attempt, the gripper rises empty while the spoon remains on the tabletop (frames 58–64, image and left_ego_image, corroborated by wrist_image). It then travels to the already-open drawer and opens its empty fingers there rather than reacquiring the spoon (frames 80–135, image and wrist_image). The return toward the spoon begins at frame 136.
- Recovery: Return to the spoon, align the fingers around a secure grasp location, and verify that the spoon lifts with the gripper before transporting it to the drawer; no human intervention is needed.
- Severity: low
- Severity evidence: The failed acquisition and empty transfer waste an attempt, but the spoon remains on the table with no visible damage.
- Resetability: immediate
- Resetability evidence: The spoon is still accessible and the drawer remains open, so the robot can retry without a human reset.
