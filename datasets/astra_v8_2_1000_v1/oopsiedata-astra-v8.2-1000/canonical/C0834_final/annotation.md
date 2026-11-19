# Episode: C0834

## Episode annotation

- Language task: pick up the corn
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the corn remains on the tabletop throughout frames 0–49. The gripper repeatedly closes and opens over the separate bowl of round produce (frames 2–15, 24–38, and 40–49), rather than acquiring the corn. The task is visibly unachieved, with task-inconsistent actions observed rather than merely an unconfirmed lift.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 2 | No |
| 2 | 50 | Yes |

## Failure annotations

### Failure 1

- Frames: 2-50
- Categories: sequencing_semantic
- Explanation: In right_shoulder_cam, the gripper starts closing over the bowl's contents at frames 2–4 and repeatedly opens and closes in that same area through frame 49. The intended corn is visibly separate on the tabletop and remains untouched. These repeated acquisition motions at the wrong location do not advance picking up the corn; possession of any bowl object is not established.
- Recovery: Open and withdraw the gripper clear of the bowl, then align with the corn on the tabletop, grasp it, and lift while checking retention. No human intervention is visibly required.
- Severity: low
- Severity evidence: No displaced objects, damage, or meaningful damage risk is established in right_shoulder_cam; the observed consequence is failure to acquire the intended target.
- Resetability: immediate
- Resetability evidence: The corn remains accessible in its original tabletop position at frame 49, and no environmental restoration is visibly needed before another attempt.