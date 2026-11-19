# Episode: C0162

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: success but suboptimal
- Outcome evidence: All three toys are on the plate after the final release (frames 749–767, wrist_cam and overhead_cam), and remain there as the arm withdraws through frame 843 (overhead_cam). Completion follows an empty grasp-and-transfer attempt and a tan-toy placement outside the plate that requires another pickup. No unwanted collision is clearly established by the images.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 192 | No |
| 192 | 350 | Yes |
| 350 | 438 | No |
| 438 | 447 | Yes |
| 447 | 844 | No |

## Failure annotations

### Failure 1

- Frames: 192-350
- Categories: grasp
- Explanation: The gripper closes beside the tan toy rather than around it (frames 192–205, wrist_cam), then travels toward the plate empty while both remaining toys stay on the table (frames 206–233, overhead_cam and wrist_cam). It continues the empty transfer and opens near the plate (frames 334–349, wrist_cam), adding no toy.
- Recovery: Reopen, align the fingers around the toy's body, and verify that the toy lifts with the gripper before transferring it; human intervention is not needed.
- Severity: low
- Severity evidence: The attempt wastes motion but leaves the toys and scene usable, with no visible damage.
- Resetability: immediate
- Resetability evidence: The missed toy remains accessible on the tabletop; another acquisition can be attempted without environmental resetting.

### Failure 2

- Frames: 438-447
- Categories: manipulation
- Explanation: After acquiring and transporting the tan toy (frames 383–430, overhead_cam), the robot opens its gripper short of the plate (frames 438–446, wrist_cam). The released toy rests on the tabletop beside the rim rather than on the plate, clearly visible in frames 447–455 in wrist_cam.
- Recovery: Regrasp the tan toy, lift it clear of the rim and other toys, and release it over an unoccupied area inside the plate; human intervention is not needed.
- Severity: low
- Severity evidence: The toy is misplaced on the table without visible damage or a meaningful damage hazard.
- Resetability: immediate
- Resetability evidence: The toy remains accessible beside the plate, so the robot can retry directly without a human reset.