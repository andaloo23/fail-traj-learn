# Episode: C0974

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: success but side effects
- Outcome evidence: The spoon is acquired and lifted in frames 75–110 (image, left_ego_image, wrist_image), but the first release at frames 191–198 leaves it on the tabletop outside the drawer. The robot reacquires it at frames 291–313, displacing the adjacent orange object during acquisition. Frames 361–367 show the spoon released into and resting inside the open drawer (image, wrist_image); it remains there through frame 399 (image).

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 191 | No |
| 191 | 199 | Yes |
| 199 | 281 | No |
| 281 | 294 | Yes |
| 294 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 191-199
- Categories: manipulation
- Explanation: After transporting the held spoon to the drawer, the robot opens its gripper outside the drawer at frames 191–192 (wrist_image). The spoon falls onto the tabletop and settles beside the orange object by frames 197–198 (image, left_ego_image), so this placement does not accomplish the task.
- Recovery: Reacquire the spoon, position it fully over the drawer interior, and lower it before releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon lands on the table and remains accessible; no breakage or meaningful damage is visible in frames 198–200.
- Resetability: immediate
- Resetability evidence: The spoon remains within the robot's workspace and can be picked up again without environmental repair or human resetting.

### Failure 2

- Frames: 281-294
- Categories: collision
- Explanation: During the second spoon acquisition, the gripper pushes and rolls the adjacent orange object away from its previous position at frames 281–293 (wrist_image, corroborated by image and left_ego_image). This is unintended movement of an unrelated object, despite the spoon acquisition subsequently succeeding.
- Recovery: Use a spoon-grasp approach that clears the orange object; restore the displaced object if its original arrangement is required, with human assistance only if autonomous replacement cannot be performed safely.
- Severity: low
- Severity evidence: The orange object is displaced on the tabletop but remains intact and on the working surface; no meaningful damage is visible.
- Resetability: minor_reset
- Resetability evidence: Returning the orange object to its previous position is a straightforward minor repositioning; no repair or difficult retrieval is required.