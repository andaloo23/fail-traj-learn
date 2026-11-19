# Episode: C0502

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot acquires and lifts the spoon in frames 93–120 (left_ego_image, wrist_image), then carries it toward the open drawer. In frames 220–228 (image, wrist_image), the spoon leaves the gripper and falls outside the drawer onto the tabletop. Frames 229–237 (image, left_ego_image) show it remaining on the table, establishing a visibly failed placement rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 220 | No |
| 220 | 229 | Yes |
| 229 | 238 | No |

## Failure annotations

### Failure 1

- Frames: 220-229
- Categories: manipulation
- Explanation: After successfully carrying the spoon to the drawer, the robot opens its gripper without placing the spoon securely inside. Frames 220–224 (wrist_image, image) show the spoon leaving the fingers and falling outside the drawer; frames 227–228 (image, left_ego_image) show it landing on the tabletop. The visible placement fails; the images do not establish a hidden cause for the misalignment.
- Recovery: Reacquire the spoon from the tabletop, align it fully over the drawer interior, lower it inside, and release only after confirming clearance from the rim. No human intervention appears necessary.
- Severity: low
- Severity evidence: The spoon falls onto the table and remains intact, with no visible damage or disruption to unrelated objects.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop and the drawer remains open, so another acquisition and placement attempt requires no environmental reset or human intervention.