# Episode: C0685

## Episode annotation

- Language task: pick up the cube
- Success label: failure
- Outcome evidence: Two acquisition attempts end with the gripper lifting away while the blue cube remains on the black mat: frames 25–34 and 76–80 in exterior_image_1_left, corroborated by wrist_image_left. The cube is still on the mat at frame 80; these are visibly failed attempts, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 25 | No |
| 25 | 35 | Yes |
| 35 | 76 | No |
| 76 | 81 | Yes |

## Failure annotations

### Failure 1

- Frames: 25-35
- Categories: grasp
- Explanation: After closing near the cube at frames 17–24, the gripper withdraws empty during frames 25–34 in exterior_image_1_left. The cube remains on the mat, also visible in wrist_image_left, establishing failed acquisition. Opening the gripper at frame 35 begins preparation for another attempt.
- Recovery: Reopen the gripper, align the fingers on opposite sides of the cube, descend to a suitable grasp height, and verify acquisition with a small lift; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The cube remains on the mat with no visible damage or harmful scene disturbance; the consequence is an unsuccessful pickup.
- Resetability: immediate
- Resetability evidence: The cube remains accessible and the environment needs no visible resetting before another attempt.

### Failure 2

- Frames: 76-81
- Categories: grasp
- Explanation: Following the second approach and finger closure, the gripper rises away during frames 76–80 in exterior_image_1_left without lifting the cube. wrist_image_left likewise shows the cube remaining beside the retreating fingers on the mat; the second acquisition fails.
- Recovery: Reopen and reposition the fingers to straddle the cube before closing, then use a small verification lift before further motion; no human intervention is visibly required.
- Severity: low
- Severity evidence: The failed acquisition leaves the cube on the mat, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The cube remains upright and accessible, so another attempt requires robot repositioning rather than environmental or human resetting.