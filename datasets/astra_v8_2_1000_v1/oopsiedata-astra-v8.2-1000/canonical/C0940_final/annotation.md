# Episode: C0940

## Episode annotation

- Language task: Place the red block on top of the yellow rectangle.
- Success label: success but suboptimal
- Outcome evidence: The first lift loses the red block, which falls back onto the table (frames 7–12, wrist_cam and right_base_cam). The robot subsequently reacquires it (frames 65–75, wrist_cam), carries it to the yellow rectangle, and releases it (frames 150–158). After withdrawal, the red block remains supported on the yellow rectangle through frame 240, visible in left_base_cam and right_base_cam, with the overlapping placement also visible in wrist_cam. The successful placement follows an unsuccessful initial acquisition/retention attempt.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 7 | No |
| 7 | 19 | Yes |
| 19 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 7-19
- Categories: grasp
- Explanation: Following the initial lift, the red block moves out from between the fingers beginning at frame 7, tips and falls back onto the tabletop in frames 9–12, and remains there while the empty gripper moves clear through frame 18 (wrist_cam and right_base_cam). The attempted lift therefore fails to retain the block for transport to the yellow rectangle; the images do not establish the underlying cause.
- Recovery: Reapproach the red block at its updated position, align the fingers around opposing faces, secure the grasp, and verify retention with a short lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The block falls a short distance onto the usable tabletop; no damage or disturbance of unrelated objects is visible in frames 9–18.
- Resetability: immediate
- Resetability evidence: The red block remains accessible on the table, so the robot can reacquire it without environmental resetting or human intervention.
