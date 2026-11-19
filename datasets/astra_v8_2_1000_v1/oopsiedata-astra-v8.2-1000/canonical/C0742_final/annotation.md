# Episode: C0742

## Episode annotation

- Language task: put the sushi in the pot
- Success label: failure
- Outcome evidence: The orange-topped, white-rice sushi remains on the table, while the robot picks up the separate yellow crosshatched object with a pale green base (frames 40–56, wrist and left). The yellow object is released into the pot at frames 113–119 (wrist); the sushi remains outside the pot in left. This is visible wrong-object placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 24 | No |
| 24 | 120 | Yes |

## Failure annotations

### Failure 1

- Frames: 24-120
- Categories: sequencing_semantic
- Explanation: By frame 24, the gripper is aligning around the yellow crosshatched object rather than the orange-and-white sushi beside it (wrist). It closes around the yellow object at frames 40–49, lifts and transports it at frames 53–100, and releases it into the pot at frames 113–119 (wrist and left). The acquisition and placement physically work, but involve the wrong object; the sushi remains on the table.
- Recovery: Remove the incorrectly placed object from the pot and return it to a clear table location, then acquire the orange-and-white sushi and place it in the pot. No human intervention appears necessary.
- Severity: low
- Severity evidence: The wrong object is placed in the pot without visible damage, spilling, or meaningful damage risk; the intended task remains undone.
- Resetability: minor_reset
- Resetability evidence: Returning the yellow object from the accessible pot to the table is a straightforward reset; no repair or difficult retrieval is visibly required.