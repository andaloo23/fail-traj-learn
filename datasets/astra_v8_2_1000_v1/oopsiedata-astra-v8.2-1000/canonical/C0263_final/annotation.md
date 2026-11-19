# Episode: C0263

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot grasps and lifts the spoon from the table (frames 80–120, image, left_ego_image, and wrist_image), then carries it toward the drawer. At frames 207–213, it releases the spoon outside the drawer, and the spoon falls onto the tabletop. The spoon remains on the table through frame 242 in image and left_ego_image; this is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 207 | No |
| 207 | 243 | Yes |

## Failure annotations

### Failure 1

- Frames: 207-243
- Categories: manipulation
- Explanation: After successfully carrying the spoon, the robot releases it above the table rather than inside the drawer at frames 207–208 (wrist_image and image). The spoon falls and settles on the tabletop by frames 213–214 (image and left_ego_image). The gripper subsequently moves away empty, with no reacquisition through frame 242. The visible failure is placement outside the intended receptacle; the underlying cause is not established.
- Recovery: Reacquire the spoon from its visible tabletop position, align it fully over the open drawer interior, lower it, and release only after confirming placement clearance. No human intervention appears necessary.
- Severity: low
- Severity evidence: The spoon lands on the table and appears intact; no damage or disruption to unrelated objects is visible.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop, allowing another grasp and placement attempt without environmental resetting or human intervention.