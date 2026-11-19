# Episode: C0963

## Episode annotation

- Language task: put the sushi in the pot
- Success label: failure
- Outcome evidence: The orange-topped, white-based sushi remains on the table in left at frames 120–173. Instead, the robot acquires the yellow waffle-patterned cone-shaped object, visible in wrist at frames 105–127, and deposits it in the pot at frames 168–173. This is visible wrong-object execution, not merely unconfirmed completion of the intended task.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 60 | No |
| 60 | 174 | Yes |

## Failure annotations

### Failure 1

- Frames: 60-174
- Categories: sequencing_semantic
- Explanation: Beginning at frames 60–65 in wrist, the gripper redirects and rotates the yellow cone-shaped object rather than acquiring the adjacent orange-and-white sushi. It continues aligning with that object through frames 73–104, closes around it at frame 105, and carries it toward the pot at frames 120–167. Frames 168–173 in wrist show the wrong object released into the pot, while left shows the sushi still on the table. Successful physical handling of this unrelated object does not advance the requested task.
- Recovery: Remove the cone-shaped object from the pot and return it to a clear tabletop location, then identify and grasp the orange-and-white sushi and place it in the pot; no human intervention appears necessary.
- Severity: low
- Severity evidence: The wrong object is relocated into the pot, but neither camera shows damage, spillage, or a meaningful damage hazard.
- Resetability: minor_reset
- Resetability evidence: Restoring the scene requires the straightforward removal and replacement of the cone-shaped object from the accessible pot; no repair or substantial rearrangement is visibly needed.