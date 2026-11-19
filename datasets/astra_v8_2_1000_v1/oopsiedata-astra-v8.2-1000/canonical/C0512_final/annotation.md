# Episode: C0512

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot acquires and lifts the spoon in frames 91–120 (image, left_ego_image, wrist_image), then carries it toward the open drawer. The spoon subsequently slips downward and falls outside the drawer in frames 166–197 (wrist_image, image). At frame 238 it remains on the tabletop near the edge, while the gripper is empty; this is a visibly failed transfer, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 166 | No |
| 166 | 239 | Yes |

## Failure annotations

### Failure 1

- Frames: 166-239
- Categories: grasp
- Explanation: After carrying the spoon toward the drawer, the robot loses retention: the spoon begins sliding downward relative to the fingers around frames 166–168 (wrist_image), falls clear in frames 189–191, and lands on the tabletop by frame 197 (image, left_ego_image). The robot continues moving empty near the drawer rather than retrieving it through frame 238. The images do not establish the underlying cause of the loss.
- Recovery: Re-localize the spoon on the tabletop, approach with clearance from the table edge and nearby objects, establish a secure grasp, and transfer it fully over the drawer interior before releasing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The spoon falls onto the tabletop and remains intact; no meaningful damage is visible to the spoon, robot, or surrounding scene.
- Resetability: immediate
- Resetability evidence: The spoon remains visible and accessible on the tabletop, so another acquisition can be attempted without environmental repair or human resetting.