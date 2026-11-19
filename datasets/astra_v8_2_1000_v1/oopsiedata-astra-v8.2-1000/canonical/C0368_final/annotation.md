# Episode: C0368

## Episode annotation

- Language task: pick up the cube
- Success label: failure
- Outcome evidence: The first acquisition visibly fails: exterior_image_1_left frames 25–35 show the gripper withdrawing empty while the blue cube remains on the mat, corroborated by wrist_image_left. The robot then approaches again and closes its fingers around the cube in frames 72–80, but neither camera establishes a completed pickup before the recording ends. Thus the first attempt visibly failed, while completion of the second attempt remains unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 25 | No |
| 25 | 36 | Yes |
| 36 | 81 | No |

## Failure annotations

### Failure 1

- Frames: 25-36
- Categories: grasp
- Explanation: After closing near the cube, the robot lifts its empty gripper away in exterior_image_1_left frames 25–35 while the cube stays on the mat. wrist_image_left frames 25–35 also show the cube separated from the withdrawing fingers, establishing failed acquisition rather than successful retention. Opening the gripper for another attempt begins at frame 36.
- Recovery: Reopen the gripper, realign the fingers on opposite sides of the cube, descend to a suitable grasp height, and verify retention during a short controlled lift; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The cube remains on the mat, with no visible damage or meaningful damage risk; the consequence is an unsuccessful pickup.
- Resetability: immediate
- Resetability evidence: The cube remains accessible and the environment is usable, so another grasp can be attempted without human resetting.