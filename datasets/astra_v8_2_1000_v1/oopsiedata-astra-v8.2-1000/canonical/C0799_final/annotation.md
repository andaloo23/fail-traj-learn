# Episode: C0799

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot grasps and lifts the spoon at frames 91–121 (image, left_ego_image, wrist_image), then carries it toward the open drawer at frames 145–193. At frames 194–203, the spoon leaves the gripper and falls outside the drawer onto the tabletop. Frames 205–219 (image, left_ego_image) show it remaining on the table beside the cabinet, establishing a visibly failed placement rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 194 | No |
| 194 | 204 | Yes |
| 204 | 220 | No |

## Failure annotations

### Failure 1

- Frames: 194-204
- Categories: grasp
- Explanation: At frames 194–198 (wrist_image, image), the previously held spoon moves downward out of the gripper outside the drawer; frames 199–203 (image, left_ego_image) show it falling and landing on the tabletop. This loss or release of the spoon fails to place it in the drawer; the images do not establish whether release was intentional or a slip.
- Recovery: Reacquire the spoon from the tabletop, lift it clear of the cabinet, align it fully over the open drawer interior, and lower it before releasing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The spoon lands on the tabletop with no visible damage or disturbance of unrelated objects.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the table and the drawer remains open, so another acquisition and placement attempt requires no environmental reset or human intervention.