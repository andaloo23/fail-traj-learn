# Episode: C0256

## Episode annotation

- Language task: put the corn on the green cloth
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the corn initially lies left of the green cloth (frame 0). The gripper closes around it (frames 25–29), but subsequently moves it farther left rather than onto the cloth (frames 50–69). At frame 69 the cloth remains empty and the corn remains between the fingers near the tabletop. Placement is not completed in the observed episode; no drop or abnormal termination is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 50 | No |
| 50 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 50-70
- Categories: manipulation
- Explanation: In right_shoulder_cam, frames 50–54 show the gripper and corn moving together leftward, away from the green cloth on the right; this displacement continues through frames 62–69 without a visible lift-and-transfer toward the destination. This sustained wrong-direction handling does not advance placement. The images do not establish why it occurs.
- Recovery: Stop the away-directed motion, verify a secure grasp and tabletop clearance, then lift and transfer the corn over the green cloth before lowering and releasing it. No human intervention is visibly required.
- Severity: low
- Severity evidence: The corn remains at the work surface between the fingers, with no visible damage, falling object, or disturbance of unrelated objects.
- Resetability: immediate
- Resetability evidence: The corn and cloth remain accessible on the table; the robot can correct its motion or reacquire the corn without an environmental reset.