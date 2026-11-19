# Episode: C0242_W01

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisional for this window: no toy is placed on the plate. In overhead_cam and wrist_cam, frames 52–66 show an acquisition attempt at the blue toy followed by empty withdrawal while the toy remains on the table. Frames 147–320 show repeated empty-arm movements without acquisition or placement. At frame 349, wrist_cam shows the empty plate and toys still outside it, while overhead_cam shows another approach underway. Later context is missing, so eventual completion is unconfirmed; the failed acquisition is directly visible. No unwanted collision is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 60 | No |
| 60 | 67 | Yes |
| 67 | 147 | No |
| 147 | 321 | Yes |
| 321 | 350 | No |

## Failure annotations

### Failure 1

- Frames: 60-67
- Categories: grasp
- Explanation: After the fingers close near the blue toy in wrist_cam frames 52–59, the gripper withdraws empty in frames 60–66; overhead_cam confirms that the blue toy remains on the tabletop. This establishes failed acquisition rather than a successful lift. The precise contact or reason for the miss is not visible.
- Recovery: Reposition above the blue toy, align the fingers around a graspable portion, descend carefully, and verify retention with a short lift before transporting it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy remains on the table, with no visible damage, spill, or disruptive collision.
- Resetability: immediate
- Resetability evidence: The toy remains accessible and the scene needs no physical resetting before another attempt.

### Failure 2

- Frames: 147-321
- Categories: task_not_attempted
- Explanation: Following repositioning toward the tan toy through frame 146, the empty gripper reverses away at frame 147 and repeatedly sweeps between the workspace and robot base without acquiring a toy. overhead_cam frames 164, 210, 240, 273, and 306 show these repeated excursions with the plate and toys unchanged; wrist_cam confirms the empty fingers and changing view. This sustained unproductive movement exceeds a brief pause or a single alignment adjustment. A renewed approach begins at frame 321.
- Recovery: Stop the repeated excursions, select one visible toy, and execute a deliberate collision-free approach and grasp with possession verification before transport; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is lost progress; no contact damage or meaningful damage risk is established by the images.
- Resetability: immediate
- Resetability evidence: The plate and toys remain available in their tabletop positions, so another attempt requires no environmental reset.