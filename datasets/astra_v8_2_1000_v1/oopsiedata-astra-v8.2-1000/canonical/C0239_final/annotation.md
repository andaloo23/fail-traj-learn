# Episode: C0239

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn in frames 34–41 and carries it toward the pot in frames 52–68. Upon release, the corn falls outside the pot in frame 72 and settles on the tabletop in frames 75–76, leaving the pot empty. This is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 72 | No |
| 72 | 77 | Yes |

## Failure annotations

### Failure 1

- Frames: 72-77
- Categories: manipulation
- Explanation: After successfully carrying the corn, the robot releases it outside the pot: right_shoulder_cam frame 72 shows the open gripper and corn falling in front of the pot, and frames 73–76 show it settling on the table. The placement therefore fails to put the corn in the intended container.
- Recovery: Reacquire the corn from its new tabletop position, align it fully within the pot opening, lower it into the pot, and release only once safely positioned. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The corn lands on the tabletop; no damage or disruption to other objects is visible in right_shoulder_cam frames 72–76.
- Resetability: immediate
- Resetability evidence: The corn remains accessible on the table and the pot remains upright and empty, allowing another attempt without an environmental reset.