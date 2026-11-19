# Episode: C0331

## Episode annotation

- Language task: close the drawer
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the drawer is open at frame 0. The robot engages its handle and moves the drawer partway inward during frames 11–23, but releases it and withdraws during frames 24–28. The drawer remains visibly protruding, with its interior exposed beneath the cabinet top, through frame 58. This is a visibly incomplete closing attempt, not merely completion hidden by occlusion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 24 | No |
| 24 | 59 | Yes |

## Failure annotations

### Failure 1

- Frames: 24-59
- Categories: manipulation
- Explanation: After controlling the handle and partially moving the drawer inward, the robot releases it at frame 24 and withdraws by frame 28 in right_shoulder_cam without finishing the closing motion. The drawer stays partially open throughout frames 29–58, with no further corrective action.
- Recovery: Reapproach the drawer and apply a controlled inward push along its sliding direction, then verify that it is fully seated before withdrawing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The drawer remains partially open, but right_shoulder_cam shows no damage, displaced unrelated objects, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The drawer remains accessible and apparently intact in its partially open position, so another closing attempt requires no environmental reset or human intervention.