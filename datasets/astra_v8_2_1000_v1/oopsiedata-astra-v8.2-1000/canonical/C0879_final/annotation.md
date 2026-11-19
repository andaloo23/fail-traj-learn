# Episode: C0879

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn from the table at frames 38–46 and carries it toward the pot at frames 60–71. It releases the corn at frame 76, but the corn falls outside the pot and settles on the table by frames 80–83. The pot remains empty; this is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 76 | No |
| 76 | 84 | Yes |

## Failure annotations

### Failure 1

- Frames: 76-84
- Categories: manipulation
- Explanation: After establishing control and transporting the corn, the robot releases it outside the pot at frame 76 in right_shoulder_cam. The corn tumbles onto the tabletop at frames 77–79 and remains there through frame 83, so the placement does not achieve the task. No corrective action is visible.
- Recovery: Reacquire the corn from its visible tabletop position, align it within the pot opening, lower it into the pot, and release only once placement is supported. No human intervention appears necessary.
- Severity: low
- Severity evidence: The corn lands and remains on the table; no damage, spill, or disruption of unrelated objects is visible in right_shoulder_cam at frames 76–83.
- Resetability: immediate
- Resetability evidence: The corn remains accessible on the tabletop and the pot remains upright and empty, allowing another attempt without environmental resetting or human intervention.