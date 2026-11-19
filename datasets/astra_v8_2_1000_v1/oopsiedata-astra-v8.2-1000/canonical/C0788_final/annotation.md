# Episode: C0788

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The spoon remains on the tabletop at frame 399 in image and left_ego_image, rather than inside the drawer. The robot makes multiple acquisition attempts: wrist_image shows the spoon separating from the fingers at frames 85–87, and later empty withdrawals at frames 313–320 and 374–391. This is a visibly unsuccessful episode, not merely unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 85 | No |
| 85 | 91 | Yes |
| 91 | 303 | No |
| 303 | 324 | Yes |
| 324 | 361 | No |
| 361 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 85-91
- Categories: grasp
- Explanation: After closing around the spoon handle, the gripper loses engagement at frames 85–87 in wrist_image. The spoon settles back onto the tabletop in left_ego_image while the empty gripper rises through frame 90, preventing acquisition for transport.
- Recovery: Reobserve the spoon’s shifted pose, align the fingers around its handle, and verify retention with a small lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon remains on the table, with no visible damage or disruption to unrelated objects.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible for another grasp without environmental resetting.

### Failure 2

- Frames: 303-324
- Categories: grasp
- Explanation: At frames 303–308, wrist_image shows the fingers closing against or beside the handle without securing it. During the subsequent lift at frames 311–320, the fingers separate from the spoon while left_ego_image shows it remaining on the table; the gripper withdraws empty.
- Recovery: Open the gripper, correct lateral alignment and grasp height, and confirm that the spoon moves with the gripper before proceeding; no human intervention is needed.
- Severity: low
- Severity evidence: The attempt fails to lift the spoon, but no damage or harmful side effect is visible.
- Resetability: immediate
- Resetability evidence: The spoon is still on the accessible tabletop and can be reattempted directly.

### Failure 3

- Frames: 361-400
- Categories: grasp
- Explanation: At frames 361–364 in wrist_image, the fingers close beside the spoon handle rather than enclosing it. The robot subsequently lifts and retreats empty at frames 374–399, while image and left_ego_image show the spoon remaining on the tabletop.
- Recovery: Return to the spoon, realign the open fingers to straddle the handle, and verify a secure acquisition before moving toward the drawer; no human intervention is needed.
- Severity: low
- Severity evidence: Only task completion is prevented; no visible damage or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The spoon and drawer remain usable, and no cleanup or manual repositioning is necessary for another attempt.