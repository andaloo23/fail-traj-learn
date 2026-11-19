# Episode: C0285

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot lifts the spoon in frames 74–107 (left_ego_image and wrist_image), but drops it onto the tabletop in frames 108–115 (all three cameras). The spoon remains outside the drawer at frame 278 (image and left_ego_image), establishing a visibly failed attempt rather than merely unconfirmed completion. The approach also displaces an unrelated white oval object.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 45 | No |
| 45 | 58 | Yes |
| 58 | 108 | No |
| 108 | 117 | Yes |
| 117 | 170 | No |
| 170 | 279 | Yes |

## Failure annotations

### Failure 1

- Frames: 45-58
- Categories: collision
- Explanation: During the spoon approach, the gripper displaces the adjacent white oval object, which moves away across the tabletop; compare frames 44–48 in image and frames 53–58 in left_ego_image. This is unintended contact with an unrelated object, not required spoon handling.
- Recovery: Adjust the approach to maintain clearance from the white object before grasping the spoon; human intervention is not needed while both objects remain accessible.
- Severity: low
- Severity evidence: The white object rolls across the table but remains on it, with no visible breakage or other damage.
- Resetability: immediate
- Resetability evidence: The displaced object does not visibly prevent another spoon attempt; restoring its exact original position is unnecessary for the task.

### Failure 2

- Frames: 108-117
- Categories: grasp
- Explanation: After visibly carrying the spoon, the gripper loses possession in frames 108–110 (wrist_image). The spoon falls and settles on the tabletop by frames 115–116 (image and left_ego_image), undoing the pickup without placing it in the drawer; the images do not establish the underlying cause.
- Recovery: Locate the spoon in its new pose, reacquire it securely, verify retention with a low lift, and transport it over the drawer before releasing; no human intervention is visibly required.
- Severity: low
- Severity evidence: The spoon falls onto the tabletop without visible damage, spilling, or damage to other objects.
- Resetability: immediate
- Resetability evidence: The intact spoon remains accessible on the table and can be grasped again without an environmental reset.

### Failure 3

- Frames: 170-279
- Categories: task_not_attempted
- Explanation: Following some repositioning toward the spoon in frames 117–169, the robot remains above the table with no meaningful acquisition or drawer-placement progress through frame 278 (image and left_ego_image). Late empty gripper opening and closing in frames 258–278 (wrist_image) does not move the spoon, which stays on the tabletop.
- Recovery: Resume a task-directed approach to the spoon’s observed position, align the fingers around its handle, and verify a secure pickup before proceeding to the drawer; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: This interval delays completion but causes no visible additional damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The scene remains usable, with the spoon accessible and no cleanup, repair, or object replacement needed.