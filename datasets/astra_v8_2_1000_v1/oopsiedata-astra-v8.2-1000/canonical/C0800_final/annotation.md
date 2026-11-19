# Episode: C0800

## Episode annotation

- Language task: Move the banana to the pot on the right and sushi to the bowl.
- Success label: failure
- Outcome evidence: In image_primary, the banana starts in the cream bowl at frame 0 and is successfully deposited in the right-hand metal pot by frames 148–151. However, the sushi remains on the tabletop and the bowl remains empty at frame 159, so the full task is not completed. Earlier banana acquisition attempts visibly fail; completion of the sushi transfer is unconfirmed rather than an observed failed sushi grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 43 | No |
| 43 | 62 | Yes |
| 62 | 101 | No |
| 101 | 118 | Yes |
| 118 | 136 | No |
| 136 | 138 | Yes |
| 138 | 160 | No |

## Failure annotations

### Failure 1

- Frames: 43-62
- Categories: grasp
- Explanation: In image_primary, the fingers close at frames 43–45, but the gripper rises empty at frames 46–48 while the banana stays in the bowl. It then travels to the pot and opens there at frames 58–59 without transferring anything. Task-directed return toward the banana begins at frame 62.
- Recovery: Return to the banana, adjust finger placement around its body, and verify acquisition with a short lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The banana remains in the bowl, with no visible damage or meaningful damage risk from the missed acquisition.
- Resetability: immediate
- Resetability evidence: The target remains accessible in its original container and another grasp can be attempted without environmental resetting.

### Failure 2

- Frames: 101-118
- Categories: grasp
- Explanation: In image_primary, the fingers repeatedly narrow and reopen around the banana at frames 101–106 without securing it. The gripper subsequently rises clear at frames 114–117 while the banana remains in the bowl, establishing another unsuccessful acquisition.
- Recovery: Reposition the open fingers to straddle a graspable section of the banana, close securely, and check that the object follows a small lift; no human intervention is needed.
- Severity: low
- Severity evidence: No object damage or spill is visible; the consequence is another unsuccessful pickup.
- Resetability: immediate
- Resetability evidence: The banana and containers remain usable and accessible without a human reset.

### Failure 3

- Frames: 136-138
- Categories: collision
- Explanation: In image_primary, the held banana/gripper assembly passes against the bowl’s right rim or handle during transfer at frames 136–137, visibly shifting the bowl rightward compared with frame 135. This displaces the container unintentionally; the exact contacting component is partly occluded.
- Recovery: Lift the banana fully above the bowl rim before continuing laterally, and update the bowl’s location before placing the sushi; no human intervention is necessary.
- Severity: low
- Severity evidence: The bowl slides but remains upright on the table, with no visible damage or spilled contents.
- Resetability: immediate
- Resetability evidence: The shifted bowl remains accessible and usable as the sushi destination, so restoring its exact original position is unnecessary for another valid attempt.