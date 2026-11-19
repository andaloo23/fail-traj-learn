# Episode: C0895

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is white and blue, and the largest bowl is the central cream-colored bowl. The robot instead repeatedly handles the pink toy on the right and ultimately deposits it in that bowl (frames 80–96). At frames 97–99, the blue toy remains on the table in its original location. This is visible wrong-object completion, not merely an unconfirmed outcome.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 8 | No |
| 8 | 34 | Yes |
| 34 | 44 | No |
| 44 | 65 | Yes |
| 65 | 72 | No |
| 72 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 8-34
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary frames 8–13, the gripper targets and closes around the right pink toy rather than the left blue toy. It shifts the pink toy but withdraws empty by frames 16–18. A second acquisition at frames 27–32 again ends with the toy on the table and the gripper retreating empty at frame 33. Both the wrong-object selection and failed retention are visible.
- Recovery: Reidentify the left blue toy, approach its body with an open gripper, and verify a secure grasp before transporting it to the cream bowl; no human intervention is needed.
- Severity: low
- Severity evidence: The pink toy is displaced on the tabletop, but no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: Both toys remain accessible on the table, and the intended task can be retried without environmental intervention.

### Failure 2

- Frames: 44-65
- Categories: collision
- Explanation: In image_primary frames 44–64, the empty gripper repeatedly moves against the cream bowl's interior or rim, shifting the bowl leftward, particularly across frames 53–58. Neither toy is acquired or transported during this interval; the bowl contact disrupts the destination rather than placing the requested toy.
- Recovery: Lift clear of the bowl, update its location, and approach the left blue toy with sufficient clearance; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The bowl slides but stays upright and visibly intact, with no spill or damage shown.
- Resetability: immediate
- Resetability evidence: The shifted bowl remains accessible and usable as the destination, so restoring its exact original position is unnecessary for another attempt.

### Failure 3

- Frames: 72-100
- Categories: sequencing_semantic
- Explanation: In image_primary frames 72–79, the robot again approaches and grasps the right pink toy. It successfully carries that toy at frames 81–94 and releases it into the cream bowl at frames 95–96. The left blue toy remains untouched through frame 99, so this successful physical transfer performs the wrong-object operation.
- Recovery: Remove the pink toy from the bowl and return it safely to the table, then grasp the left blue toy and place it in the largest bowl; autonomous correction appears feasible without human intervention.
- Severity: low
- Severity evidence: The wrong toy is placed in the bowl, but no object damage or meaningful damage risk is visible.
- Resetability: minor_reset
- Resetability evidence: Returning the pink toy from the bowl to the table is a straightforward reset that restores the initial object arrangement; no repair or difficult retrieval is needed.