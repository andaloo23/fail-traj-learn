# Episode: C0351_W04

## Episode annotation

- Language task: pick up cup with one arm, hand over to the other arm, and place it on saucer
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window: aria at frames 1050, 1150, 1250 and 1399 shows the cup upright on the table, without pickup, handover or placement. left_wrist and right_wrist show essentially unchanged empty gripper configurations with only small positional changes across those frames. The visible local failure is sustained lack of task progress, not a demonstrated failed grasp. Earlier execution beyond the two context frames and later execution are unavailable, so the outcome is provisional.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1400 | Yes |

## Failure annotations

### Failure 1

- Frames: 1050-1400
- Categories: task_not_attempted
- Explanation: Throughout this approximately 11.7-second window, the arms remain hovering away from the cup with only slight drift; no discernible cup-directed approach or acquisition occurs. aria at frames 1050, 1150, 1250 and 1399 shows the cup unchanged on the tabletop, while left_wrist and right_wrist show no held cup or productive handover action. This sustained unproductive interval supports stalling rather than a brief pause. The preceding two context frames show a similar pose but cannot establish its earlier duration; the failure may extend beyond either window edge.
- Recovery: Resume a cup-directed approach with one arm, align and acquire the cup, verify retention, then perform the handover and saucer placement; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only task progress is prevented; no displaced objects, damage or concrete risk of damage is visible in aria or the wrist views.
- Resetability: immediate
- Resetability evidence: The cup remains upright and the visible environment is unchanged, allowing another attempt without an environmental reset or human intervention.