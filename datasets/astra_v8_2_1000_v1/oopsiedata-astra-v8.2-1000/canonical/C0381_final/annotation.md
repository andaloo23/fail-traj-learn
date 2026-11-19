# Episode: C0381

## Episode annotation

- Language task: Fold the yellow cloth.
- Success label: failure
- Outcome evidence: The cloth starts spread out on the table (frame 0, overhead_cam and wrist_cam). The robot acquires and lifts part of it (frames 136–170), but subsequent movement gathers it into irregular overlapping bunches rather than a completed fold (frames 177–249, both cameras). After release, the cloth remains rumpled on the table through frame 395 in overhead_cam; wrist_cam also shows the uneven result at frames 295–305. This is a visibly unsuccessful folding attempt, not merely an outcome hidden by the recording ending.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 177 | No |
| 177 | 250 | Yes |
| 250 | 396 | No |

## Failure annotations

### Failure 1

- Frames: 177-250
- Categories: manipulation
- Explanation: After establishing control of the cloth, the robot moves the held portion while the remaining fabric bunches and overlaps irregularly (frames 177–224, overhead_cam and wrist_cam). Continued movement does not align the cloth into a fold, and opening the gripper leaves a rumpled arrangement on the table (frames 243–249, both cameras). Possession was established; the visible failure is the folding manipulation, not a missed acquisition.
- Recovery: Spread the cloth flat again, identify corresponding edges or corners, and lift and place one side over the other before smoothing the fold; human intervention is not inherently needed.
- Severity: low
- Severity evidence: The cloth is rumpled but remains on the usable tabletop; no tearing, damage, or disturbance of unrelated objects is visible.
- Resetability: minor_reset
- Resetability evidence: A straightforward flattening and repositioning of the cloth would restore the starting arrangement; no repair or difficult retrieval is needed, and this reset could be performed by the robot or a person.