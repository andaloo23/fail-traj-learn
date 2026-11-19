# Episode: C0853

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The spoon remains on the yellow plate from frame 0 through frame 375 in image and left_ego_image, with its final position also clearly visible in wrist_image. The robot approaches the spoon but then spends most of the episode hovering nearby with small positional changes; no acquisition or transfer into the drawer is visible. This is an observed lack of task progress, not an unconfirmed placement or a demonstrated completed grasp miss.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 63 | No |
| 63 | 376 | Yes |

## Failure annotations

### Failure 1

- Frames: 63-376
- Categories: task_not_attempted
- Explanation: After the initial approach, the gripper remains near the spoon with only small adjustments rather than progressing to acquisition or placement. Frames 63, 100, 168, 240, 300 and 375 in left_ego_image and wrist_image show this prolonged hovering, while image confirms that the spoon stays on the yellow plate. The sustained unproductive interval lasts about 26 seconds; no completed failed acquisition or hardware malfunction is established.
- Recovery: Reassess the spoon’s position, align the fingers around its handle, and perform a controlled grasp followed by a verified lift and transfer into the open drawer. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no displaced unrelated objects, damage, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the plate and the scene is unchanged, so another acquisition attempt requires no environmental reset or human intervention.