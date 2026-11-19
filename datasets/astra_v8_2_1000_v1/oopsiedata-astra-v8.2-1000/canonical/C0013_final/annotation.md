# Episode: C0013

## Episode annotation

- Language task: Fold the yellow cloth.
- Success label: failure
- Outcome evidence: The cloth starts spread on the table (frame 0, overhead_cam and wrist_cam). The robot acquires and lifts part of it at frames 310–333, but the subsequent placement leaves irregular overlapping flaps and a bunched section rather than a completed fold (frames 405–418, both cameras). The cloth remains in that state after the gripper withdraws through frame 470 in overhead_cam; this is a visibly unsuccessful folding attempt, not merely an unconfirmed acquisition.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 340 | No |
| 340 | 414 | Yes |
| 414 | 471 | No |

## Failure annotations

### Failure 1

- Frames: 340-414
- Categories: manipulation
- Explanation: After establishing control of the cloth, the robot draws the lifted portion into uneven overlapping flaps rather than aligning it over the remaining cloth (frames 340–377, overhead_cam and wrist_cam). It lowers and releases this bunched arrangement at frames 398–413, leaving a curled section and misaligned layers instead of completing the fold.
- Recovery: Reacquire an exposed edge, spread the cloth flat, then bring one edge over to the opposite edge and smooth the fold before releasing; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The cloth is left rumpled on the tabletop; neither camera shows tearing, damage, or disruption to other objects.
- Resetability: minor_reset
- Resetability evidence: Returning to a clean starting state requires spreading and flattening the cloth, a straightforward reset that could be performed by the robot or a person without repair or retrieval.