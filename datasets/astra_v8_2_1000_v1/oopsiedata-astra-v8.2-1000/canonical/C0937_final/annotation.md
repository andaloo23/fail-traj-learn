# Episode: C0937

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed initially (frame 0, image and left_ego_image). The robot approaches and progressively aligns its gripper near the door/handle area (frames 40, 160, 240, and 280, image and left_ego_image), but no door-opening motion is visible. At frame 297, image and left_ego_image still show the door closed while the arm remains nearby; wrist_image provides no confirmation of an opening. Completion is therefore unconfirmed in the observed episode, rather than an established failed grasp or pull. The slow approach and alignment do not independently establish a local failure.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 298 | No |

## Failure annotations

None