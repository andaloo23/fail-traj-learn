# Episode: C0842

## Episode annotation

- Language task: close the drawer
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the drawer is open at frame 0. The robot approaches its handle/front during frames 1–20, but the drawer shifts farther outward at frames 21–22 rather than closing. It remains visibly open at frame 27; closure is not merely occluded or unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 21 | No |
| 21 | 23 | Yes |
| 23 | 28 | No |

## Failure annotations

### Failure 1

- Frames: 21-23
- Categories: manipulation
- Explanation: In right_shoulder_cam frames 21–22, the drawer front and handle move outward with the gripper relative to the stationary cabinet, exposing more of the drawer interior. This moves the drawer opposite the required closing direction. Subsequent frames show repositioning and slight inward movement, but not completed closure.
- Recovery: Align contact with the drawer’s closing direction and gently push it inward, then verify that the front is seated against the cabinet; no human intervention is visibly required.
- Severity: low
- Severity evidence: The drawer remains open and usable; no damage, tipping, or other harmful consequence is visible.
- Resetability: immediate
- Resetability evidence: The drawer remains accessible in its cabinet and can be pushed closed without an environmental reset or human intervention.