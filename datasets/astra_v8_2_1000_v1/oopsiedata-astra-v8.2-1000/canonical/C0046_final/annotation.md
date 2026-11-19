# Episode: C0046

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The spoon is not placed in the drawer. The first acquisition leaves it on the table (frames 53–94, left_ego_image and wrist_image); a later lift ends with the spoon falling back onto the table (frames 169–179, all three cameras). The robot subsequently opens its empty gripper over the drawer (frames 275–290, wrist_image), then returns toward the spoon. At frame 397, left_ego_image and wrist_image still show the spoon on the tabletop; the final renewed approach is unfinished, not an additional confirmed failed grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 53 | No |
| 53 | 96 | Yes |
| 96 | 169 | No |
| 169 | 191 | Yes |
| 191 | 275 | No |
| 275 | 291 | Yes |
| 291 | 398 | No |

## Failure annotations

### Failure 1

- Frames: 53-96
- Categories: grasp
- Explanation: The fingers finish closing beside the spoon rather than securing it (frames 53–60, wrist_image). The gripper then rises empty while the spoon remains on the tabletop (frames 61–94, left_ego_image and wrist_image), establishing failed acquisition.
- Recovery: Reopen the fingers, realign around a graspable part of the spoon, and verify a secure hold with a small lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon remains on the table with no visible damage or harmful disturbance.
- Resetability: immediate
- Resetability evidence: The spoon is accessible for another grasp without environmental resetting.

### Failure 2

- Frames: 169-191
- Categories: grasp
- Explanation: Following the successful lift visible at frames 160–168, the spoon slides downward relative to the fingers at frames 169–173 and separates from them at frame 174 (wrist_image). It falls onto the table at frames 175–179 while the empty gripper continues withdrawing (image and left_ego_image), losing the acquired object before delivery.
- Recovery: Return to the spoon's new position, establish a more secure grasp, and verify retention before moving toward the drawer; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon lands on the tabletop without visible breakage or damage to nearby objects.
- Resetability: immediate
- Resetability evidence: Although displaced and reoriented, the spoon remains reachable on the table and can be reacquired without intervention.

### Failure 3

- Frames: 275-291
- Categories: sequencing_semantic
- Explanation: The robot opens its empty gripper over the drawer in a placement-like action (frames 275–281, wrist_image) and remains there through frame 290, although the spoon is visibly still on the table in image and left_ego_image. This release cannot deliver the required object.
- Recovery: Check possession before attempting placement, return to acquire the spoon, and transport it into the open drawer before releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The empty release does not visibly damage or disturb the drawer or other objects; it only fails to advance placement.
- Resetability: immediate
- Resetability evidence: The drawer remains open and the spoon remains accessible, so no environmental reset is required.