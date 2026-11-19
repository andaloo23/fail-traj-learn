# Episode: C0150

## Episode annotation

- Language task: pour the coffee beans into the cup
- Success label: success but side effects
- Outcome evidence: The robot acquires and lifts the light-blue bean container (frames 30–80, left and right), then tilts it over the brown cup on the black base. Beans visibly accumulate in the brown cup during frames 145–167 (left and right), but others scatter onto the surrounding tabletop. Some beans remain in the held container at frame 167 (wrist), so complete emptying is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 148 | No |
| 148 | 168 | Yes |

## Failure annotations

### Failure 1

- Frames: 148-168
- Categories: manipulation
- Explanation: During the pour, beans escape beyond the receiving cup and scatter across the table, first visibly evident around frame 148 and increasingly clear in frames 151–167 (left and right). The robot retains the source container (wrist), but does not fully contain the poured beans within the cup.
- Recovery: Rotate the source container upright to stop the flow, then realign its lip closer above the cup before continuing with a controlled tilt. Collect the scattered beans; human assistance may be needed if the robot cannot collect them.
- Severity: low
- Severity evidence: Dry beans scatter onto the tabletop, but no damage, broken containers, or meaningful damage risk is visible.
- Resetability: minor_reset
- Resetability evidence: The spilled beans need straightforward collection and return to a suitable container; the cup, source container, and work surface remain usable.