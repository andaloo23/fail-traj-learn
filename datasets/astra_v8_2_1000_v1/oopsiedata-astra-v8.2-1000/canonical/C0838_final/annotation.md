# Episode: C0838

## Episode annotation

- Language task: put the corn on the green cloth
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the gripper approaches the corn at frames 2–8 but moves away without it at frames 9–29. The corn remains on the bare tabletop beside the green cloth through frame 57; placement is visibly not achieved, rather than merely hidden or unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 9 | No |
| 9 | 58 | Yes |

## Failure annotations

### Failure 1

- Frames: 9-58
- Categories: grasp
- Explanation: In right_shoulder_cam, after approaching closely at frames 6–8, the gripper moves past and away from the corn starting at frame 9 without acquiring it. Frames 12–29 increasingly reveal the empty gripper separated from the unchanged corn. It remains away from the target through frame 57, with no renewed acquisition or placement attempt. The visible evidence supports a missed acquisition, not a drop or a known mechanical cause.
- Recovery: Reapproach the corn, align the fingers on opposite sides, close securely, and verify possession before lifting and transferring it onto the green cloth; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The corn and cloth remain in place, and right_shoulder_cam shows no damage, displaced unrelated objects, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The corn remains accessible on the tabletop and the cloth is unobstructed, so another attempt requires no environmental reset or human intervention.