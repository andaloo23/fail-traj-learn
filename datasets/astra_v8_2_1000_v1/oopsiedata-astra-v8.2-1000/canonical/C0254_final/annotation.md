# Episode: C0254

## Episode annotation

- Language task: Put the kiwi into the bowl.
- Success label: success but side effects
- Outcome evidence: The robot grasps and transports the brown kiwi in frames 89–138 (wrist_cam and right_base_cam), releases it into the bowl in frames 140–145 (wrist_cam), and withdraws with the kiwi remaining inside in frames 150–240 (right_base_cam). After completing the task, it descends toward the unrelated yellow-and-green corn and closes its fingers around it, visibly nudging it in frames 196–240 (wrist_cam); successful lifting of the corn is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 196 | No |
| 196 | 241 | Yes |

## Failure annotations

### Failure 1

- Frames: 196-241
- Categories: sequencing_semantic
- Explanation: After the kiwi is already in the bowl, the robot begins a further descent toward the unrelated corn at frame 196, approaches it through frames 200–215, and closes its fingers around it in frames 216–218 (wrist_cam and left_base_cam). The corn shifts during this interaction and the subsequent movement through frame 240 (wrist_cam). This unnecessary wrong-object interaction does not advance the completed kiwi task; possession of the corn is not confirmed.
- Recovery: Open the fingers and withdraw clear of the corn, leaving the kiwi in the bowl, then stop the task. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The unrelated corn is nudged on the tabletop, but no damage, falling object, or meaningful damage risk is visible in wrist_cam or either base camera through frame 240.
- Resetability: immediate
- Resetability evidence: All objects remain accessible on the tabletop and the kiwi remains in the bowl; the robot can disengage without a human environmental reset.