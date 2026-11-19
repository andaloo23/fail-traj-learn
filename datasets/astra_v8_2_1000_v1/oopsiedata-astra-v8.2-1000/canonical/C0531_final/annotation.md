# Episode: C0531

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot repeatedly approaches the upper drawer but withdraws without opening it. In wrist_image, the fingers close above/beside the silver handle at frames 100–106, 231–235 and 360–366, then retreat empty. The drawer fronts remain closed in left_ego_image at frames 0, 143, 270 and 399. This is a visibly unsuccessful sequence of acquisition attempts, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 100 | No |
| 100 | 137 | Yes |
| 137 | 231 | No |
| 231 | 261 | Yes |
| 261 | 360 | No |
| 360 | 390 | Yes |
| 390 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 100-137
- Categories: grasp
- Explanation: In wrist_image at frames 100–106, the fingers close without enclosing the silver drawer handle, which remains below the grasp location. The robot withdraws empty during frames 115–136 while the drawer stays closed in left_ego_image, establishing failed acquisition.
- Recovery: Reopen the gripper, align the fingers around the handle with sufficient clearance, and verify acquisition before pulling along the drawer travel direction; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed; no damage or displacement of unrelated objects is visible.
- Resetability: immediate
- Resetability evidence: The cabinet and handle remain in place, allowing another approach without environmental resetting.

### Failure 2

- Frames: 231-261
- Categories: grasp
- Explanation: wrist_image at frames 231–235 shows another closure above/beside the handle rather than around it. During frames 246–260 the closed fingers retreat without the handle, and left_ego_image shows no drawer opening.
- Recovery: Correct the grasp position relative to the visible handle rather than repeating the same offset, then verify a secure hold before a controlled pull; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Only task progress is lost; no visible damage or harmful scene change results.
- Resetability: immediate
- Resetability evidence: The failed grasp leaves the environment usable and unchanged, with no object repositioning required.

### Failure 3

- Frames: 360-390
- Categories: grasp
- Explanation: In wrist_image at frames 360–366, the fingers again close away from the silver handle. Frames 374–389 show withdrawal with empty fingers while the handle remains on the closed drawer, corroborated by left_ego_image.
- Recovery: Reassess the handle position and approach orientation, place the handle between the fingers, and confirm retention before pulling; no human intervention is established as necessary.
- Severity: low
- Severity evidence: The drawer remains closed and intact, with no observed damage or disturbance to surrounding objects.
- Resetability: immediate
- Resetability evidence: Another corrected acquisition can be attempted without resetting the cabinet or surrounding scene.