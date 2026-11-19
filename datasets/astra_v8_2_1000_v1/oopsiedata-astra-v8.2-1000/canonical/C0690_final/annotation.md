# Episode: C0690

## Episode annotation

- Language task: put the bowl on the table
- Success label: failure
- Outcome evidence: In frames 0–38, cameras left and wrist show the robot approaching the orange bowl in the wire rack. The bowl remains in the rack through frame 102, with no visible lift, transfer, or placement onto the clear tabletop. Frames 39–102 show sustained lack of progress near the rack; completion is unconfirmed, but a completed failed grasp or drop is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 39 | No |
| 39 | 103 | Yes |

## Failure annotations

### Failure 1

- Frames: 39-103
- Categories: task_not_attempted
- Explanation: After approaching the bowl, the robot remains almost stationary near the rack throughout frames 39–102 in cameras left and wrist. Small pose changes around frames 68–77 do not produce visible acquisition or movement of the bowl toward the table. This sustained unproductive interval interrupts the task; the images do not establish a failed completed grasp or a mechanical cause.
- Recovery: Reassess the bowl rim and rack clearance, reposition the gripper for an unobstructed grasp, verify acquisition, then lift clear of the rack and place the bowl on the table. No human intervention is visibly required.
- Severity: low
- Severity evidence: The bowl remains supported in the rack, and neither camera shows damage, spilling, or another harmful consequence; the visible consequence is lack of task progress.
- Resetability: immediate
- Resetability evidence: The bowl and surrounding scene remain available for another attempt without visible need for environmental resetting or human intervention.