# Episode: C0160

## Episode annotation

- Language task: put the sushi in the pot
- Success label: failure
- Outcome evidence: The orange-topped, white-based sushi remains on the table in left at frames 60–119. Instead, the robot grasps the yellow waffle-textured, green-and-white-ended object (wrist, frames 48–67), carries it to the pot, and releases it into the pot at frames 118–119 in wrist. This is visible wrong-object handling, not merely unconfirmed task completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 48 | No |
| 48 | 120 | Yes |

## Failure annotations

### Failure 1

- Frames: 48-120
- Categories: sequencing_semantic
- Explanation: At frame 48 in wrist, the gripper closes around the yellow waffle-textured object rather than the adjacent orange-and-white sushi. Frames 60–85 in left and wrist show the yellow object being transported while the sushi remains on the table. The robot continues this wrong-object transfer and releases the yellow object into the pot at frames 118–119 in wrist; successful physical handling does not satisfy the requested sushi placement.
- Recovery: Remove the wrong object from the pot and return it to a clear table location, then acquire the orange-and-white sushi and place it in the pot. Human intervention is not visibly necessary if both objects remain safely reachable.
- Severity: low
- Severity evidence: The wrong object is relocated into the pot, but no damage, spill, or meaningful damage risk is visible in left or wrist through frame 119.
- Resetability: minor_reset
- Resetability evidence: Restoring the original scene requires a straightforward removal of the wrong object from the accessible pot and replacement on the table; no repair or difficult retrieval is indicated.