# Episode: C0812

## Episode annotation

- Language task: pour the coffee beans into the cup
- Success label: success but side effects
- Outcome evidence: The robot acquires and lifts the light-blue bean container (frames 36–84, left and right), then pours beans into the brown cup on the black platform (frames 121–144, right). By frames 145–163, wrist shows the source container visibly emptied and right shows beans in the receiving cup, but also several beans scattered across the tabletop. The transfer is completed with spillage.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 127 | No |
| 127 | 145 | Yes |
| 145 | 164 | No |

## Failure annotations

### Failure 1

- Frames: 127-145
- Categories: manipulation
- Explanation: During the controlled pour, beans scatter outside the receiving cup onto the table, visibly established at frame 127 and increasing through frames 130–144 in right, with scattered beans also visible in left. The robot retains the source container, but the pour fails to contain all beans within the destination.
- Recovery: Return the source container upright and set it down securely; collect the spilled beans before another attempt, using human assistance if the robot cannot reliably collect small loose objects. For a subsequent pour, position the source rim closer to and centered over the receiving cup and tilt gradually.
- Severity: low
- Severity evidence: A small number of dry beans spill onto the tabletop; no breakage, equipment damage, or meaningful damage risk is visible.
- Resetability: minor_reset
- Resetability evidence: The scattered beans require straightforward collection and, for a fresh attempt, reloading into the source container; no repair or difficult retrieval is visibly required.