# Episode: C0336

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn in frames 33–40 and carries it toward the pot in frames 49–68. On release at frame 69, the corn falls outside the pot and rests on the table in frames 70–72, leaving the pot empty. This is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 69 | No |
| 69 | 73 | Yes |

## Failure annotations

### Failure 1

- Frames: 69-73
- Categories: manipulation
- Explanation: After establishing control and carrying the corn to the pot, the robot releases it at frame 69 in right_shoulder_cam; it falls outside the pot and settles on the tabletop in frames 70–72. The placement fails to put the corn inside the intended container.
- Recovery: Regrasp the corn from the table, align it fully over the pot opening, and lower it into a supported position before releasing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The corn remains on the tabletop, with no visible damage, spill, or disturbance of unrelated objects in right_shoulder_cam frames 70–72.
- Resetability: immediate
- Resetability evidence: The corn is accessible on the table and the pot remains upright and usable, allowing another attempt without environmental resetting or human intervention.