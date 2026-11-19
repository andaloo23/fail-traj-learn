# Episode: C0443

## Episode annotation

- Language task: Stack the purple cube on top of the green block.
- Success label: failure
- Outcome evidence: The robot approaches and aligns with the purple cube in frames 0–128 (left_base_cam, right_base_cam, wrist_cam), then closes around it and lifts it in frames 129–152. It subsequently carries the cube toward the green block in frames 153–240. At frame 240, wrist_cam still shows the purple cube between the gripper fingers, while right_base_cam shows the gripper at the block location; no released, independently supported stack is visible. Completion is therefore unconfirmed in the observed episode, rather than a visibly failed placement. The slow alignment and transport do not establish a local failure, and the recording ending does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 241 | No |

## Failure annotations

None