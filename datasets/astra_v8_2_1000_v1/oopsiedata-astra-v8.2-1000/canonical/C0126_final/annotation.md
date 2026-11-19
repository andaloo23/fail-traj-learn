# Episode: C0126

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot acquires and lifts the spoon, but it slips from the gripper and falls onto the table at frames 91–98 (wrist_image, left_ego_image, image). The robot subsequently moves toward the drawer without the spoon. At frame 341, the spoon remains on the tabletop outside the drawer (image, left_ego_image), establishing visible noncompletion rather than merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 91 | No |
| 91 | 99 | Yes |
| 99 | 170 | No |
| 170 | 342 | Yes |

## Failure annotations

### Failure 1

- Frames: 91-99
- Categories: grasp
- Explanation: The lifted spoon slides downward relative to the fingers starting at frame 91, leaves the gripper at frames 95–96, and settles on the tabletop by frame 98 (wrist_image, left_ego_image, image). Loss of retention prevents its transport to the drawer; the underlying cause is not visible.
- Recovery: Relocate the spoon on the table, align the fingers around a secure portion of its handle, and verify retention with a small lift before transporting it to the open drawer; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon falls a short distance onto the tabletop and remains intact and accessible, with no visible damage or disruption to unrelated objects.
- Resetability: immediate
- Resetability evidence: The spoon can be grasped again directly from its new tabletop position without environmental resetting or human intervention.

### Failure 2

- Frames: 170-342
- Categories: task_not_attempted
- Explanation: After moving to the drawer, the robot remains essentially in the same position through frame 341, with occasional empty gripper opening and closing but no return to the spoon or placement progress (image and left_ego_image, frames 170, 220, 280, 341; wrist_image, frames 256–263 and 301–307). This sustained unproductive interval leaves the spoon on the table.
- Recovery: Resume task-directed action by locating and securely reacquiring the spoon, ensuring sufficient drawer opening, and placing it inside; no human intervention is visibly required.
- Severity: low
- Severity evidence: The interval prevents task completion but causes no visible damage, spill, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The spoon and drawer remain accessible and the scene remains usable; another task-directed attempt needs no environmental reset.