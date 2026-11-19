# Episode: C0036

## Episode annotation

- Language task: take the spoon out of the mug and place it to the left of the plate
- Success label: failure
- Outcome evidence: The spoon initially stands in the mug (frame 0, left and wrist). After unsuccessful acquisition attempts, the robot visibly lifts it out at frames 92–95 (left and wrist), but releases it onto the plate beside the mug at frames 104–108 (wrist). It remains on the plate through frame 119, rather than to the left of the plate; this is a visibly incorrect placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 31 | No |
| 31 | 58 | Yes |
| 58 | 66 | No |
| 66 | 84 | Yes |
| 84 | 104 | No |
| 104 | 120 | Yes |

## Failure annotations

### Failure 1

- Frames: 31-58
- Categories: grasp
- Explanation: Following closure near the spoon at frame 30, the gripper withdraws empty at frames 31–36 while the spoon remains in the mug (left and wrist). It then lowers beside the mug and opens without having acquired the spoon at frames 37–57 (left and wrist), so this motion does not transport the target.
- Recovery: Reapproach the exposed spoon, align the fingers around it, and verify possession with a small controlled lift before transporting it; no human intervention is indicated.
- Severity: low
- Severity evidence: The spoon remains in the upright mug, with no visible damage or spill.
- Resetability: immediate
- Resetability evidence: The target remains accessible in its original container; no environmental reset is needed.

### Failure 2

- Frames: 66-84
- Categories: grasp
- Explanation: After another closure near the spoon at frames 64–65, the gripper lifts without extracting it at frame 66, continues unsuccessful movements near it, and opens and withdraws at frames 76–84 while the spoon remains in the mug (left and wrist).
- Recovery: Reposition the open gripper around the spoon's exposed section and confirm secure acquisition before lifting clear of the mug; no human intervention is indicated.
- Severity: low
- Severity evidence: The unsuccessful acquisition leaves the spoon in the mug without visible damage or other meaningful disruption.
- Resetability: immediate
- Resetability evidence: The mug and spoon remain available for another attempt without manual resetting.

### Failure 3

- Frames: 104-120
- Categories: sequencing_semantic
- Explanation: After successfully extracting the spoon at frames 92–95, the robot opens its fingers at frames 104–105 and leaves the spoon resting on the plate beside the mug, then retracts (frames 106–119, left and wrist). Placement on the plate does not satisfy placement to the left of the plate.
- Recovery: Reacquire the spoon from the plate and place it on the clear countertop to the plate's left, verifying the final spatial relationship before withdrawing; no human intervention is indicated.
- Severity: low
- Severity evidence: The spoon is deposited on the plate without visible breakage, spilling, or damage; the consequence is incorrect task placement.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the plate and can be picked up directly for correction without an environmental reset.