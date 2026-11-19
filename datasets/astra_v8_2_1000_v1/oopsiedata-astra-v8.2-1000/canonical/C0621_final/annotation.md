# Episode: C0621

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot makes three spoon acquisition attempts but never transports it into the drawer. In wrist_image and left_ego_image, the spoon slips out during the first two lifts (frames 79–89 and 187–195); the third lift leaves it on the table (frames 310–330). At frame 392, image and left_ego_image still show the spoon on the tabletop outside the drawer, establishing visible failure rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 79 | No |
| 79 | 90 | Yes |
| 90 | 187 | No |
| 187 | 196 | Yes |
| 196 | 310 | No |
| 310 | 330 | Yes |
| 330 | 393 | No |

## Failure annotations

### Failure 1

- Frames: 79-90
- Categories: grasp
- Explanation: After lifting the spoon, the robot loses retention: wrist_image shows the handle sliding down through the fingers from frame 79 and separating by frame 84; left_ego_image shows the spoon falling and settling on the tabletop through frame 89, preventing transport to the drawer.
- Recovery: Re-localize the spoon, grasp farther along the handle with adequate finger engagement, and verify retention with a short low lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon falls onto the clear tabletop with no visible damage or disturbance to unrelated objects.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the table, so another grasp can be attempted without environmental resetting.

### Failure 2

- Frames: 187-196
- Categories: grasp
- Explanation: The second acquisition again loses the spoon during lifting: wrist_image shows the handle sliding toward the fingertips at frames 187–190 and separating at frame 191; left_ego_image shows it falling back onto the table at frames 192–195 instead of being carried to the drawer.
- Recovery: Adjust the grasp position and finger alignment rather than repeating the same shallow hold, then verify a stable low lift; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon drops onto the tabletop without visible breakage or other consequential disturbance.
- Resetability: immediate
- Resetability evidence: The dropped spoon remains reachable and intact in the visible views; no manual reset is required.

### Failure 3

- Frames: 310-330
- Categories: grasp
- Explanation: The third closing attempt fails to secure the spoon: wrist_image shows the fingers closing at the end of the handle around frames 310–313, while left_ego_image shows the gripper lifting away empty through frames 314–329 with the spoon remaining on the tabletop.
- Recovery: Reopen the gripper, align both fingers around a substantial section of the handle, and confirm that the spoon rises with the gripper before proceeding toward the drawer; no human intervention is needed.
- Severity: low
- Severity evidence: This attempt leaves the spoon on the table with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The scene remains usable and the spoon is accessible for an immediate revised acquisition attempt.
