# Episode: C0601

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: success but suboptimal
- Outcome evidence: The robot sorts the carrot, brown food-shaped object and orange into the light-blue bowl, and the pink rabbit and blue elephant toys into the green bowl. wrist_cam frames 1086–1090 show all five objects separated into these groups; overhead_cam and wrist_cam frame 1131 show the stable final arrangement. A failed initial acquisition of the blue elephant precedes its successful retry and placement (frames 664–695 and 774–837).

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 664 | No |
| 664 | 695 | Yes |
| 695 | 1132 | No |

## Failure annotations

### Failure 1

- Frames: 664-695
- Categories: grasp
- Explanation: During the first blue-elephant acquisition, the toy moves away from the fingertips rather than becoming secured (wrist_cam frames 664–674). The robot subsequently raises the closed, empty gripper while the toy remains on the tabletop, confirming failed acquisition (overhead_cam and wrist_cam frames 678–694). Reopening for recovery begins at frame 695.
- Recovery: Reopen the gripper, realign its fingers around the elephant's body at its updated position, and confirm secure acquisition with a small lift before transporting it to the green bowl; no human intervention is needed.
- Severity: low
- Severity evidence: The toy remains on the table without visible damage; the observed consequence is an unsuccessful pickup and delay.
- Resetability: immediate
- Resetability evidence: The elephant remains accessible for another grasp, and neither bowl nor the other objects requires resetting.