# Episode: C0700

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot grasps and lifts the spoon in frames 55–90 (image, left_ego_image, wrist_image), then carries it toward the open drawer. During release in frames 154–165, the spoon falls outside the drawer, across the tabletop edge and out of view (image); wrist_image shows the gripper opening beside the drawer. This is a visibly failed placement, not merely unconfirmed completion. No subsequent retrieval or successful placement is visible through frame 171.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 154 | No |
| 154 | 166 | Yes |
| 166 | 172 | No |

## Failure annotations

### Failure 1

- Frames: 154-166
- Categories: manipulation
- Explanation: After carrying the acquired spoon to the drawer, the robot opens its gripper without the spoon being safely contained over the drawer interior (frames 154–158, wrist_image). The spoon falls outside the drawer, descends across the table, and passes over the near edge in frames 159–165 (image), defeating the intended placement. Its final resting location is not visible.
- Recovery: Stop and locate the fallen spoon; human assistance is needed if it is outside the robot's safe reachable workspace. Retrieve it, then align the entire spoon over the open drawer interior before lowering and releasing it.
- Severity: low
- Severity evidence: The spoon falls off the table, but no breakage, damage to other objects, or concrete meaningful damage risk is visible; its condition after leaving view is unconfirmed.
- Resetability: minor_reset
- Resetability evidence: The spoon must be located and returned to a reachable position for another attempt, likely requiring a simple human retrieval; the images do not establish an obstructed landing location or a need for repair.