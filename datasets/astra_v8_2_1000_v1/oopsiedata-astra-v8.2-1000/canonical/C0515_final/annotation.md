# Episode: C0515

## Episode annotation

- Language task: pick up the corn
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the corn remains on the tabletop in the same position throughout frames 0–49. The gripper repeatedly closes and opens over the separate bowl of colorful objects instead (e.g., frames 2–3, 17–20, and 30–33), then remains there through frame 49. The task visibly remains undone; this is not merely an occluded or unconfirmed lift.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 2 | No |
| 2 | 50 | Yes |

## Failure annotations

### Failure 1

- Frames: 2-50
- Categories: sequencing_semantic
- Explanation: Starting at frame 2 in right_shoulder_cam, the gripper closes over objects in the bowl rather than the clearly separate corn on the tabletop. It repeatedly opens and closes at that location (frames 13–20 and 25–38), then stays there through frame 49 without approaching or lifting the corn. This wrong-target operation does not advance the task; possession of any bowl object is not established.
- Recovery: Open and withdraw the gripper clear of the bowl, identify the corn on the tabletop, and align for a grasp of the corn before closing and lifting. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The corn remains untouched and no damage, spillage, or meaningful damage risk is visible in right_shoulder_cam through frame 49.
- Resetability: immediate
- Resetability evidence: The corn remains accessible in its original tabletop position, and no environmental restoration is visibly required before another attempt.