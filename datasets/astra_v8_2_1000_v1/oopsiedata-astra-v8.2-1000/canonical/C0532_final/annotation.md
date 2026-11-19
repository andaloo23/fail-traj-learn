# Episode: C0532

## Episode annotation

- Language task: pick up the blue peg and insert it into the green peghole
- Success label: failure
- Outcome evidence: In front and side frames 0–29, the blue peg remains beside the green peghole while the robot approaches. In wrist and side frames 30–36, the fingers close around the green peghole rather than the blue peg. Frames 37–66 show no further progress, with the blue peg still separate on the table. The requested pickup and insertion are visibly not achieved; this is not merely an occluded or unconfirmed insertion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 30 | No |
| 30 | 67 | Yes |

## Failure annotations

### Failure 1

- Frames: 30-67
- Categories: sequencing_semantic
- Explanation: In wrist frames 30–36, the gripper centers on and closes around the green peghole instead of acquiring the blue peg, which remains separately visible on the table in side. The robot then remains in that configuration through frame 66 without picking up or inserting the blue peg. This is a wrong-object acquisition attempt; lifting or secure possession of the green object is not established.
- Recovery: Open the fingers without displacing the green peghole, retract, and realign around the blue peg; verify its acquisition before lifting and aligning it with the green opening. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The task is prevented from succeeding, but side and wrist frames 36–66 show no visible damage, toppling, or other harmful consequence.
- Resetability: immediate
- Resetability evidence: Both objects remain accessible on the tabletop, with no visible environmental disturbance requiring a reset; the robot can release and reposition for another attempt.