# Episode: C0758

## Episode annotation

- Language task: close the drawer
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the drawer is open at frame 0. The gripper works around its handle through frames 4–40, then lifts away without the handle or substantial drawer closure in frames 41–57. The drawer remains visibly extended with its interior exposed at frame 69. Thus closure is visibly not achieved, rather than merely hidden or unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 41 | No |
| 41 | 58 | Yes |
| 58 | 70 | No |

## Failure annotations

### Failure 1

- Frames: 41-58
- Categories: grasp
- Explanation: In right_shoulder_cam, after closing its fingers around the handle region in frames 27–40, the gripper rises away in frames 41–57 without acquiring the handle; the handle stays on the visibly open drawer. This completed unsuccessful acquisition does not advance closure. The subsequent opening and repositioning beginning at frame 58 is consistent with preparation for another attempt.
- Recovery: Reposition in front of the drawer and establish a stable pushing contact aligned with its sliding direction, then gently push it closed and verify closure; human intervention is not visibly needed.
- Severity: low
- Severity evidence: The drawer remains open, but right_shoulder_cam shows no damage, displaced unrelated objects, or meaningful damage risk from the missed acquisition.
- Resetability: immediate
- Resetability evidence: The drawer and handle remain accessible and intact in frames 52–57, allowing another attempt without environmental resetting or human intervention.