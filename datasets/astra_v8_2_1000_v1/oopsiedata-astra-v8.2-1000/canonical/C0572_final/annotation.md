# Episode: C0572

## Episode annotation

- Language task: take the spoon out of the mug and place it to the left of the plate
- Success label: failure
- Outcome evidence: The spoon initially stands in the mug (frame 0, left and wrist). After unsuccessful acquisition attempts, the robot visibly lifts it out at frames 92–95, but releases it onto the plate beside the mug rather than to the left of the plate (frames 104–109, wrist and left). It remains on the plate through frame 119; this is a visibly incorrect placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 31 | No |
| 31 | 54 | Yes |
| 54 | 66 | No |
| 66 | 85 | Yes |
| 85 | 104 | No |
| 104 | 120 | Yes |

## Failure annotations

### Failure 1

- Frames: 31-54
- Categories: grasp
- Explanation: Following closure near the spoon at frame 30, the gripper withdraws empty at frames 31–35 while the spoon remains standing in the mug, visible in left and wrist. It then lowers beside the mug and moves its fingers over the plate without the spoon through frame 53, making no placement progress.
- Recovery: Reopen and align the fingers around the exposed spoon, acquire it securely, and verify that it moves with the gripper before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon remains in the mug, and neither camera establishes damage, spillage, or another harmful consequence.
- Resetability: immediate
- Resetability evidence: The target remains accessible in the upright mug; no environmental reset is needed before another attempt.

### Failure 2

- Frames: 66-85
- Categories: grasp
- Explanation: After another closure at frames 64–65, the gripper lifts without extracting the spoon at frame 66 and makes further unsuccessful movements around it through frame 75. It opens and withdraws at frames 76–84 while the spoon remains in the mug (left and wrist), establishing unsuccessful acquisition rather than merely an unfinished closure.
- Recovery: Approach the exposed spoon with corrected finger alignment, close securely, and confirm retention during a short vertical lift before proceeding; human intervention is not needed.
- Severity: low
- Severity evidence: The attempt does not remove the spoon, but no damage or spill is visible in left or wrist.
- Resetability: immediate
- Resetability evidence: The mug stays upright and the spoon remains available for a direct retry without resetting the scene.

### Failure 3

- Frames: 104-120
- Categories: sequencing_semantic
- Explanation: After successfully extracting and carrying the spoon at frames 92–103, the robot opens its fingers at frames 104–105 and leaves the spoon resting on the plate beside the mug, clearly visible in wrist at frames 106–112. It withdraws through frame 119 without correcting the placement; the requested destination was to the left of the plate, not on it.
- Recovery: Reacquire the spoon from the plate, move it fully beyond the plate’s left edge onto the counter, and release it in a stable position; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon is placed at the wrong location, with no visible damage, breakage, or spillage.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the plate and can be picked up directly for corrective placement without human resetting.