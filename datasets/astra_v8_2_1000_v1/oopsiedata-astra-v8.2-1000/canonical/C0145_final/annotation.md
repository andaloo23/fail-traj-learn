# Episode: C0145

## Episode annotation

- Language task: stack the yellow block on the blue blocks
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the gripper approaches the loose yellow block at frames 9–18, then closes and withdraws without it at frames 20–28. The yellow block and the two central blue blocks remain on the table, separate and unchanged through frame 69. This is a visibly unsuccessful acquisition followed by sustained inactivity, not merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 18 | No |
| 18 | 35 | Yes |
| 35 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 18-35
- Categories: grasp
- Explanation: In right_shoulder_cam, the fingers close beside the far end of the yellow block during frames 18–21 rather than securing it. The closed gripper moves away toward the bowl at frames 22–34 while the yellow block remains in its original position, establishing a missed acquisition.
- Recovery: Open the gripper, realign the fingers on opposite sides of the loose yellow block, lower to a suitable grasp height, and verify acquisition before transporting it to the blue blocks; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The block remains on the tabletop, and no damage, dropping, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The yellow block and blue blocks remain available in their original arrangement; another acquisition can be attempted without environmental resetting.

### Failure 2

- Frames: 35-70
- Categories: task_not_attempted
- Explanation: In right_shoulder_cam, the gripper opens near the bowl at frames 35–37 and then remains approximately there through frame 69, with only small adjustments. This sustained interval produces no renewed approach to the loose yellow block or progress toward stacking it on the blue blocks.
- Recovery: Resume a task-directed approach to the loose yellow block, acquire it securely, and place it stably across the blue blocks; no human intervention is established as necessary.
- Severity: low
- Severity evidence: The visible consequence is lack of task progress; no damage or significant hazard is shown.
- Resetability: immediate
- Resetability evidence: The required blocks remain accessible and undisturbed, so no physical scene reset is needed before resuming.
