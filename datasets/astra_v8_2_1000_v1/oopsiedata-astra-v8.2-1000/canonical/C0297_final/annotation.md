# Episode: C0297

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: success but suboptimal
- Outcome evidence: The first acquisition misses: frames 74–110 in wrist_image and left_ego_image show the closed gripper withdrawing empty while the wooden spoon remains beside the orange plate. After realignment, frames 196–225 in left_ego_image show the spoon lifted and transported toward the open drawer. Frames 248–254 in image and wrist_image show its release into the drawer, where it remains through frame 267. Completion follows one failed grasp; no unintended side effect is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 74 | No |
| 74 | 121 | Yes |
| 121 | 268 | No |

## Failure annotations

### Failure 1

- Frames: 74-121
- Categories: grasp
- Explanation: At frame 74, wrist_image shows the fingers closed beside, rather than around, the spoon. During frames 84–110, the gripper rises and withdraws empty while the spoon remains on the table, clearly visible in wrist_image and left_ego_image. This completed acquisition attempt does not move the target toward the drawer; the gripper reopens for realignment at frame 121.
- Recovery: Reopen the gripper, align the fingers on opposite sides of the spoon handle, descend and grasp, then verify that the spoon lifts before transporting it to the drawer; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon remains on the tabletop, and no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible in its original area, so another grasp can be attempted without environmental resetting or human intervention.