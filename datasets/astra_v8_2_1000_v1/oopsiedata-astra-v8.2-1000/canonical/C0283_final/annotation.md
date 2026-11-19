# Episode: C0283

## Episode annotation

- Language task: put the corn on the green cloth
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the gripper approaches the corn at frames 2–11, but the corn turns and remains on the tabletop outside the fingers at frames 12–18. The gripper subsequently moves away empty, while the corn remains beside the unoccupied green cloth through frame 53. This is a visibly failed acquisition with no completed placement, rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 12 | No |
| 12 | 54 | Yes |

## Failure annotations

### Failure 1

- Frames: 12-54
- Categories: grasp
- Explanation: In right_shoulder_cam at frame 12, the corn turns out of the grasp region and remains on the table behind the fingers. Across frames 13–24, the gripper moves farther from it without possession; through frames 25–53 it continues away and then remains away without reacquiring the corn. The acquisition fails and no transport to the cloth occurs.
- Recovery: Reapproach the corn at its updated position and orientation, align the fingers around its sides, and verify a secure grasp with a small lift before transporting and releasing it onto the green cloth. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The corn remains on the tabletop, and no damage or disruption to surrounding objects is visible in right_shoulder_cam through frame 53.
- Resetability: immediate
- Resetability evidence: The corn and cloth remain accessible and usable; the robot can retry from the corn’s current position without an environmental reset or human intervention.