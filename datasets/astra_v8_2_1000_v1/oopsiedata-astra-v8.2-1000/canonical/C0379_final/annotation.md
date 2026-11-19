# Episode: C0379

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The spoon remains on the tabletop throughout the episode, including frames 0, 53, 100 and 128 in image and left_ego_image. The robot approaches it but then withdraws empty toward the drawer; wrist_image at frames 48–76 shows the spoon separating from the empty gripper. This is a visibly unsuccessful acquisition and transfer attempt, not merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 39 | No |
| 39 | 129 | Yes |

## Failure annotations

### Failure 1

- Frames: 39-129
- Categories: grasp
- Explanation: Starting around frame 39, the gripper moves away from its near-spoon acquisition position without carrying the spoon. By frames 48–53, wrist_image clearly shows the spoon outside the fingers, while image and left_ego_image confirm it remains on the table. The subsequent empty movement toward the drawer does not transfer the spoon; it is still on the tabletop at frame 128. No successful possession or subsequent drop is visible.
- Recovery: Return to the spoon, align the fingers around a graspable portion, close them and verify that the spoon lifts with the gripper before moving to the open drawer and releasing it inside. No human intervention appears necessary.
- Severity: low
- Severity evidence: The spoon remains on the usable tabletop, and no damage, falling objects or harmful collision is visible.
- Resetability: immediate
- Resetability evidence: The spoon and drawer remain available for another attempt; no environmental restoration or human reset is visibly needed.