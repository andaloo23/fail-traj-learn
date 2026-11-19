# Episode: C0012

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: success but suboptimal
- Outcome evidence: The first acquisition fails: frames 90–110 in image and left_ego_image show the gripper lifting away while the spoon remains on the tabletop. A second attempt lifts the spoon successfully (frames 175–190, left_ego_image and wrist_image). The robot then carries it to the open drawer and releases it; frames 253–259 in wrist_image show the spoon resting inside the drawer beneath the withdrawn, empty gripper. No unrelated side effect is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 90 | No |
| 90 | 111 | Yes |
| 111 | 260 | No |

## Failure annotations

### Failure 1

- Frames: 90-111
- Categories: grasp
- Explanation: After closing near the spoon, the robot raises and withdraws its gripper without acquiring it. The separation develops from frame 90 and is clear by frames 103–110 in left_ego_image and image, where the spoon remains on the table; wrist_image also shows the spoon outside the closed fingers. This lift does not advance the transfer.
- Recovery: Reopen the gripper, realign the fingers around the spoon, and retry acquisition, verifying that the spoon lifts with the gripper before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon remains on the usable tabletop, with no visible damage or harmful disturbance to surrounding objects.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible for another grasp, so no environmental reset or human intervention is required.