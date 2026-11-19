# Episode: C0759_W04

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisional for this window: the robot acquires and carries the blue toy toward the plate at frames 1088–1172, but releases it outside the plate at frames 1173–1182 (overhead_cam, wrist_cam). The pink and tan toys are visible on the plate, while the blue toy remains beside it. Another acquisition is underway at frames 1393–1399, without confirmed lifting or placement (wrist_cam). Thus a failed placement is visible, and eventual completion remains unconfirmed; earlier and later execution are not supplied.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1173 | No |
| 1173 | 1185 | Yes |
| 1185 | 1223 | No |
| 1223 | 1333 | Yes |
| 1333 | 1400 | No |

## Failure annotations

### Failure 1

- Frames: 1173-1185
- Categories: manipulation
- Explanation: After carrying the blue toy toward the plate, the robot opens its fingers at frames 1173–1176 and releases the toy outside the rim; it tumbles and settles on the tabletop beside the plate by frames 1180–1184 (overhead_cam, wrist_cam). This is an unsuccessful placement after established object control, rather than an unconfirmed grasp.
- Recovery: Reacquire the blue toy, lift it clear of the rim, position it fully above a free area of the plate, and lower it before releasing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The toy lands on the tabletop and remains accessible, with no visible damage or meaningful damage risk established.
- Resetability: immediate
- Resetability evidence: The robot can retry from the toy’s visible position beside the plate without environmental resetting.

### Failure 2

- Frames: 1223-1333
- Categories: task_not_attempted
- Explanation: Following an approach toward the misplaced blue toy at frames 1185–1222, the open, empty gripper moves away over bare tabletop at frames 1223–1255 and remains there with little change through approximately frame 1332, leaving the toy beside the plate (overhead_cam, wrist_cam). This retreat and sustained unproductive pause do not advance acquisition; movement back toward the toy becomes evident from frame 1333.
- Recovery: Resume a direct, clearance-preserving approach to the blue toy, align the fingers around its body, and verify a retained grasp before transporting it onto the plate; no human intervention is visibly required.
- Severity: low
- Severity evidence: The interval delays completion but shows no damage, unwanted object displacement, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy and plate remain available in their existing positions, so another attempt requires no scene reset.