# Episode: C0138

## Episode annotation

- Language task: pick up the blue peg and insert it into the green peghole
- Success label: failure
- Outcome evidence: The robot approaches the objects in frames 0–31 (front, side, wrist), but then remains beside the green peghole with only small pose changes. The blue peg stays on the table outside the hole through frame 164 (side, wrist). No pickup or insertion is visible; the observed failure is sustained lack of progress, not a confirmed failed grasp or abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 32 | No |
| 32 | 165 | Yes |

## Failure annotations

### Failure 1

- Frames: 32-165
- Categories: task_not_attempted
- Explanation: After approaching, the robot remains nearly stationary beside the green peghole for the rest of the episode, with small adjustments that do not visibly advance acquisition. Frames 32, 60, 100, 130 and 164 (side, wrist) show the blue peg still separately on the table and no established possession; front confirms the sustained low arm pose. This prolonged unproductive interval goes beyond a brief preparation pause.
- Recovery: Re-localize the blue peg, move the open gripper into a clear grasp alignment, acquire and verify retention, then align the peg with the green hole and insert it. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but neither object is visibly damaged or knocked over, and no meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: Both objects remain accessible on the tabletop in frame 164 (side); another acquisition attempt requires no visible environmental reset or human intervention.