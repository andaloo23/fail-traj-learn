# Episode: C0463

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven starts open at frame 0 in image and left_ego_image. The robot raises the door toward the oven during frames 62–79, but subsequently moves it outward again rather than leaving it shut. In image at frames 300, 360 and 399, the door remains angled away from the oven body; wrist_image also shows the displaced door close to the gripper. Thus the observed attempt leaves the oven ajar, rather than merely ending before completion can be checked.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 159 | No |
| 159 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 159-400
- Categories: manipulation
- Explanation: After raising the oven door nearly upright during frames 62–79, the robot moves the controlled door outward again from approximately frame 159 onward. Comparing image at frames 159, 230, 300 and 399 shows the door increasingly angled away from the body instead of seated closed; wrist_image shows the corresponding door movement beside the gripper. The final door position does not satisfy closing the oven. The images do not establish a hidden mechanical or planning cause.
- Recovery: Guide the door back toward the oven along its hinge motion, gently seat it closed, then disengage without pulling it outward and visually verify that it stays shut; no human intervention is visibly required.
- Severity: low
- Severity evidence: The door remains ajar, but no breakage, displaced unrelated objects or other meaningful damage is visible in image or left_ego_image through frame 399.
- Resetability: immediate
- Resetability evidence: The oven and door remain accessible and apparently intact; another controlled closing attempt can begin without an environmental reset or demonstrated need for human assistance.