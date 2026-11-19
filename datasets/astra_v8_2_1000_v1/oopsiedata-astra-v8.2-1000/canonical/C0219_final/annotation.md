# Episode: C0219

## Episode annotation

- Language task: put the corn on the green cloth
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the corn starts on the tabletop apart from the green cloth (frame 0). The gripper approaches but displaces the corn without visibly securing it (frames 20–24). At frames 25–27, the corn remains on the bare tabletop and the cloth is empty, establishing an unsuccessful attempt rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 20 | No |
| 20 | 28 | Yes |

## Failure annotations

### Failure 1

- Frames: 20-28
- Categories: grasp
- Explanation: In right_shoulder_cam, frames 20–23 show the corn rotating and shifting beside the outside of the gripper rather than being secured between its fingers. By frame 24, it has moved leftward onto the bare tabletop, while the gripper remains empty through frame 27. This near-object acquisition attempt displaces the corn instead of acquiring it for placement; no established possession or subsequent drop is visible.
- Recovery: Re-localize the corn in its new position, open and align the fingers on opposite sides, then grasp and verify retention before lifting and placing it on the green cloth. No human intervention appears necessary.
- Severity: low
- Severity evidence: The corn is displaced on the tabletop, but no damage or meaningful damage risk is visible in right_shoulder_cam through frame 27.
- Resetability: immediate
- Resetability evidence: The corn remains accessible on the tabletop and the cloth remains clear; another aligned acquisition attempt can begin without environmental resetting or human intervention.