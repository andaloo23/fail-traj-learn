# Episode: C0753

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: success but side effects
- Outcome evidence: In image_primary, the left toy is the blue-and-white stuffed toy and the largest bowl is the white handled bowl (frame 0). The robot lifts that toy in frames 74–76 and releases it inside the white bowl by frame 87. Before acquisition, it spends a sustained interval hovering and oscillating without progress (frames 9–41). During transfer, the white bowl slides rightward and displaces the neighboring wooden bowl (frames 78–81), an unintended scene disturbance.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 9 | No |
| 9 | 42 | Yes |
| 42 | 78 | No |
| 78 | 82 | Yes |
| 82 | 88 | No |

## Failure annotations

### Failure 1

- Frames: 9-42
- Categories: task_not_attempted
- Explanation: In image_primary frames 9–41, the open gripper repeatedly makes small back-and-forth movements over the space between the bowls and the pink toy, without approaching or acquiring the intended left toy. Both toys remain stationary throughout this sustained unproductive interval. Task-directed movement toward the left toy resumes at frame 42.
- Recovery: Move toward the blue-and-white left toy, align the fingers around it, and acquire it before transferring it to the white bowl; no human intervention is needed.
- Severity: low
- Severity evidence: This interval wastes time but shows no object displacement, damage, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toys and bowls remain in place, so the robot can continue without environmental resetting.

### Failure 2

- Frames: 78-82
- Categories: collision
- Explanation: In image_primary frames 78–81, while the robot carries the toy across the white bowl's rim, the white bowl slides rightward into the wooden bowl, which also shifts rightward. This unwanted contact disturbs an unrelated bowl rather than simply placing the toy; the exact contacting robot or toy surface is partially obscured.
- Recovery: Stop lateral pressure, lift the held toy clear of the rim, and align above the white bowl's new opening before lowering and releasing it. No human intervention appears necessary.
- Severity: low
- Severity evidence: Both bowls remain upright on the table, with no visible breakage or spill; the observed consequence is minor displacement.
- Resetability: minor_reset
- Resetability evidence: Restoring the original scene requires straightforward repositioning of the two shifted bowls, with no repair or difficult retrieval needed.