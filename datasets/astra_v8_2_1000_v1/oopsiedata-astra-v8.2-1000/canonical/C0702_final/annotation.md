# Episode: C0702

## Episode annotation

- Language task: Stack and pack the cups.
- Success label: failure
- Outcome evidence: In base_image, the robot arranges the cups into a pyramid during frames 700–1000, then begins nesting them during frames 1100–1400. The final cup tips sideways during release at frames 1487–1509 instead of nesting onto the standing cups. It rolls toward the lower image boundary by frame 1600 and is out of view at frames 1627–1628. Packing is visibly unsuccessful, rather than merely unconfirmed; the loose cup’s eventual location and any fall off the table are not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1487 | No |
| 1487 | 1509 | Yes |
| 1509 | 1629 | No |

## Failure annotations

### Failure 1

- Frames: 1487-1509
- Categories: manipulation
- Explanation: In base_image at frames 1487–1488, the held cup begins tilting during the left gripper’s release over the standing cups. By frames 1507–1509, it has fallen sideways onto the table rather than nesting, preventing completion of packing. The subsequent gripper withdrawal clears the objects; the cup’s continued rolling is a consequence of the failed placement, not a separate failure.
- Recovery: Locate the loose cup and, if safely reachable, reacquire and reorient it, align it concentrically over the nested cups, and verify stable seating before releasing. Human assistance is needed if the cup has moved outside the robot’s safe reachable workspace.
- Severity: low
- Severity evidence: The cup topples and rolls on the tabletop in base_image at frames 1507–1600, with no visible damage or spill. Its disappearance below the image boundary by frames 1627–1628 does not establish a fall off the table or damage.
- Resetability: minor_reset
- Resetability evidence: Returning the loose cup to an accessible, properly oriented position requires straightforward retrieval and repositioning if it remains nearby. Its final location is outside the camera view, so greater retrieval difficulty or a definite need for human intervention cannot be established.