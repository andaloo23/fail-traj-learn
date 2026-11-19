# Episode: C0666

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The spoon remains on the tabletop throughout, including frames 0, 120, and 290 in image and left_ego_image. Instead, the robot closes its fingers beside the yellow-handled, broad wooden utensil (frames 78–113, wrist_image), then withdraws empty. No spoon acquisition or drawer placement occurs; this is visible noncompletion, not merely an occluded placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 53 | No |
| 53 | 114 | Yes |
| 114 | 126 | No |
| 126 | 241 | Yes |
| 241 | 291 | No |

## Failure annotations

### Failure 1

- Frames: 53-114
- Categories: sequencing_semantic, grasp
- Explanation: From frame 53 the robot lowers toward the yellow-handled, broad wooden utensil rather than the separate round-bowled spoon visible in left_ego_image. It contacts and shifts that wrong utensil during frames 78–105, closes beside it, and begins lifting empty during frames 110–113 (wrist_image and image). The utensil remains on the table, confirming unsuccessful acquisition as well as wrong-object targeting.
- Recovery: Withdraw clear of the tabletop, identify the round-bowled spoon, align the fingers around its handle, and verify possession before transporting it to the open drawer; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The wrong utensil is slightly repositioned on the table, but no damage, spill, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: Both utensils remain accessible on the tabletop; the robot can attempt the correct object without an environmental reset.

### Failure 2

- Frames: 126-241
- Categories: task_not_attempted
- Explanation: After withdrawing, the empty gripper remains above the tabletop with small pose changes and repeated opening and closing, without acquiring anything or approaching the drawer with the spoon (frames 126, 170, 210–240, image and wrist_image). This sustained interval does not advance the task. More substantial renewed movement begins around frame 241.
- Recovery: Re-localize the spoon and resume a deliberate approach to its handle, avoiding further empty gripper cycling; no human intervention is visibly required.
- Severity: low
- Severity evidence: The interval wastes execution time but causes no visible damage or additional object displacement.
- Resetability: immediate
- Resetability evidence: The spoon and open drawer remain available, and no cleanup, repair, or manual repositioning is needed to resume.