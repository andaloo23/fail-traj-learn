# Episode: C0729

## Episode annotation

- Language task: insert the purple peg into a hole
- Success label: failure
- Outcome evidence: The robot grasps and lifts the purple peg, then carries it toward a corner hole (front and wrist, frames 55–120). It makes small positioning adjustments near the hole through frame 200, but on opening the gripper the peg moves away from the opening and falls outside it (wrist, frames 201–206). The final views do not show insertion; this is a visibly unsuccessful release rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 201 | No |
| 201 | 207 | Yes |

## Failure annotations

### Failure 1

- Frames: 201-207
- Categories: grasp
- Explanation: As the fingers open, the peg slides out of their hold without being seated in the hole (wrist, frames 201–203). Its exposed tip then moves clear of the circular opening and the peg falls outside the fixture rather than remaining inserted (wrist and front, frames 204–206).
- Recovery: Locate the peg and confirm that it has settled, then reacquire it and align its tip centrally over a hole before lowering and verifying insertion prior to release; no human intervention is visibly required.
- Severity: low
- Severity evidence: The peg falls a short distance within the tabletop workspace; no damage to the peg, fixture, or robot is visible.
- Resetability: immediate
- Resetability evidence: The peg remains visible beside the fixture in the wrist view at frame 206, with no evident obstruction or damage requiring an environmental reset; the robot can attempt reacquisition.