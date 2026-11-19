# Episode: C0286

## Episode annotation

- Language task: pick up the corn
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the corn lies separately on the tabletop at frame 0 and remains there through frame 49. The gripper repeatedly opens and closes over the bowl and its contents instead (frames 1–49), never visibly approaching or lifting the corn. This is visible task-inconsistent behavior, not merely an unconfirmed pickup at the recording end.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1 | No |
| 1 | 50 | Yes |

## Failure annotations

### Failure 1

- Frames: 1-50
- Categories: sequencing_semantic
- Explanation: In right_shoulder_cam, the fingers begin closing over the bowl's contents at frame 1, away from the clearly separate corn. Repeated opening, closing, and repositioning remain concentrated around the bowl through frames 5–21, 22–38, and 39–49. These actions target the wrong scene region and do not advance picking up the corn; possession of any bowl object is not established.
- Recovery: Open and withdraw the gripper clear of the bowl, then align around the corn on the tabletop, close securely, and lift while verifying retention. No human intervention is visibly required.
- Severity: low
- Severity evidence: The corn remains untouched, and no damage, spill, or overturned object is visible in right_shoulder_cam through frame 49.
- Resetability: immediate
- Resetability evidence: The corn remains accessible in its original tabletop position, and no environmental restoration is visibly necessary before a corrected attempt.