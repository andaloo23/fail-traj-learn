# Episode: C0670

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: Frames 0–60 in wrist_image and left_ego_image show approach to the wooden spoon beside the orange plate. Frames 70–179 show the robot lifting and transporting the plate and its green contents along with the spoon. At frames 181–191 in image, left_ego_image and wrist_image, the plate is tilted at the open drawer and the spoon remains visible near the gripper and drawer edge; a completed placement of the spoon inside the drawer is not confirmed. This is an unconfirmed core-task completion with a visible unintended-object handling failure, rather than a confirmed successful placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 70 | No |
| 70 | 192 | Yes |

## Failure annotations

### Failure 1

- Frames: 70-192
- Categories: grasp
- Explanation: Starting at frame 70 in wrist_image and left_ego_image, the orange plate tilts and its green contents shift as the gripper acquires the plate together with the adjacent spoon. Frames 90–179 show the unrelated plate being lifted and carried toward the drawer, rather than an isolated spoon transfer. At frames 181–191 in image and left_ego_image, the plate remains tilted at the drawer opening. The unintended additional acquisition disrupts the requested spoon-only placement; the exact contact arrangement is partly occluded.
- Recovery: Lower and support the plate and its contents on a clear tabletop before releasing or separating the grasp, then acquire only the spoon and place it fully inside the drawer. Human assistance is needed only if the objects cannot be safely disentangled autonomously.
- Severity: low
- Severity evidence: The plate and its contents are visibly displaced and tilted, but no breakage, spill, or other meaningful damage is visible through frame 191.
- Resetability: minor_reset
- Resetability evidence: Returning the plate and its contents from the drawer opening to the tabletop and separating the spoon would restore a valid attempt state; this appears to require straightforward repositioning, not repair, although the final support arrangement is partly occluded.