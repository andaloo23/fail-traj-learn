# Episode: C0752

## Episode annotation

- Language task: Close the oven.
- Success label: success but suboptimal
- Outcome evidence: The door starts open in frame 0 (left_ego_image). The robot partially raises it, pauses for several seconds, and the door returns downward at frames 145–148 before a renewed closing movement. By frames 219–230 the door is upright against the oven front, and it remains closed through frame 356 (left_ego_image), with the gripper withdrawing in image and wrist_image. No unrelated object damage or displacement is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 44 | No |
| 44 | 124 | Yes |
| 124 | 145 | No |
| 145 | 159 | Yes |
| 159 | 357 | No |

## Failure annotations

### Failure 1

- Frames: 44-124
- Categories: task_not_attempted
- Explanation: After partially raising the door, the robot remains essentially stationary with the oven still open throughout frames 44–123 (image and left_ego_image); wrist_image likewise shows no substantial movement. This sustained pause does not advance closure.
- Recovery: Resume a controlled closing motion along the door’s hinge arc while maintaining suitable contact; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is delayed completion; no damage or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The door remains accessible and the surrounding scene unchanged, so continuation requires no environmental reset.

### Failure 2

- Frames: 145-159
- Categories: manipulation
- Explanation: The previously raised door rotates back downward at frames 145–148 and remains open through frame 158 (left_ego_image and image), undoing the earlier closing progress. The door edge also moves into wrist_image; the images do not establish whether grip loss or deliberate release caused the reversal.
- Recovery: Re-establish stable contact with the door or handle and guide it upward until fully seated, verifying closure before withdrawing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The door returns to an open position without visible breakage, displaced contents, or damage to nearby objects.
- Resetability: immediate
- Resetability evidence: The open door is still accessible for another closing attempt, with no cleanup or manual repositioning required.