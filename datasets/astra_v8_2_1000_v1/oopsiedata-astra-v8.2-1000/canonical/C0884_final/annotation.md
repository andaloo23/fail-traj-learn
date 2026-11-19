# Episode: C0884

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The spoon remains on the tabletop outside the open drawer in image and left_ego_image at frames 0, 54, and 119. The robot approaches but then hovers without acquiring or transporting it; wrist_image likewise shows no spoon held. Completion is visibly absent, with sustained nonprogress rather than a confirmed failed grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 54 | No |
| 54 | 120 | Yes |

## Failure annotations

### Failure 1

- Frames: 54-120
- Categories: task_not_attempted
- Explanation: After the initial approach, the gripper remains hovering near the spoon with only small positional changes through frame 119. In image and left_ego_image at frames 54, 80, 100, and 119, the spoon stays untouched on the table and no acquisition or drawer placement follows. This extended nonprogress establishes sustained stalling; wrist_image does not establish contact or a completed grasp attempt.
- Recovery: Resume task-directed alignment over the spoon, lower the open fingers around its handle, acquire and verify a secure grasp, then transfer and release it inside the open drawer. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The task remains incomplete, but no object displacement, damage, or meaningful damage risk is visible during the stall.
- Resetability: immediate
- Resetability evidence: The spoon and drawer remain available for another attempt, with no environmental reset or human intervention visibly required.