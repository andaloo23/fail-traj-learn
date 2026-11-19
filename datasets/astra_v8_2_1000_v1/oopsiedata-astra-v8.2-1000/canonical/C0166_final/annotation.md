# Episode: C0166

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed at frame 0 in image and left_ego_image. The robot approaches and gradually aligns its gripper near the door/handle region (frames 50, 150, 250, and 332 in image and wrist_image), but no door-opening motion is visible; left_ego_image still shows the closed door at frame 332. Completion is therefore unconfirmed in the observed episode, rather than a visibly completed grasp-and-pull attempt failing. The slow task-directed positioning does not establish a local failure.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 333 | No |

## Failure annotations

None