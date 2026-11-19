# Episode: C0589

## Episode annotation

- Language task: Pick up the spoon and place it into the box.
- Success label: failure
- Outcome evidence: The right gripper repeatedly closes and withdraws empty while the spoon remains on the table (ceiling and wrist_left, frames 56–77, 99–114, 159–172, and 206–221). The left gripper subsequently acquires and begins lifting the spoon (wrist_left and wrist_right, frames 285–300), but placement into the blue box is not observed. Completion is unconfirmed at the recording end, in addition to the visibly failed earlier acquisitions.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 62 | No |
| 62 | 78 | Yes |
| 78 | 100 | No |
| 100 | 115 | Yes |
| 115 | 163 | No |
| 163 | 173 | Yes |
| 173 | 208 | No |
| 208 | 222 | Yes |
| 222 | 301 | No |

## Failure annotations

### Failure 1

- Frames: 62-78
- Categories: grasp
- Explanation: After closing near the spoon, the right gripper lifts and withdraws without it; the spoon remains on the tabletop (wrist_left and ceiling, frames 62–77). The closed fingers visible in wrist_right do not retain the spoon.
- Recovery: Reopen, align the fingers around the spoon at tabletop height, and verify acquisition with a small lift before transporting it; human intervention is not needed.
- Severity: low
- Severity evidence: The spoon remains on the table with no visible damage or disruptive displacement.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible and the scene needs no physical reset before another grasp.

### Failure 2

- Frames: 100-115
- Categories: grasp
- Explanation: The right gripper completes another closure beside the spoon and retreats empty, leaving the spoon stationary (wrist_left and ceiling, frames 100–114; closed fingers in wrist_right).
- Recovery: Reopen and correct the grasp position rather than repeating the same offset closure; confirm that the spoon moves with the gripper before proceeding. No human intervention is needed.
- Severity: low
- Severity evidence: Only acquisition fails; no damage or meaningful environmental disruption is visible.
- Resetability: immediate
- Resetability evidence: The spoon and box remain in usable positions, allowing an autonomous reattempt without scene resetting.

### Failure 3

- Frames: 163-173
- Categories: grasp
- Explanation: Following another closure, the right gripper moves away from the spoon without lifting it (wrist_left and ceiling, frames 163–172). The spoon remains visibly separate from the closed gripper.
- Recovery: Reopen and adjust the approach or use the other gripper to obtain a better alignment, then verify a secure lift; human intervention is not needed.
- Severity: low
- Severity evidence: The failed grasp leaves the spoon intact on the tabletop; no harmful side effect is observed.
- Resetability: immediate
- Resetability evidence: No object restoration or cleanup is required to attempt acquisition again.

### Failure 4

- Frames: 208-222
- Categories: grasp
- Explanation: The right gripper again withdraws after closing near the spoon, but the spoon stays on the table (wrist_left and ceiling, frames 208–221). This is another completed empty acquisition rather than an unfinished finger closure.
- Recovery: Reopen and select a corrected grasp, potentially with the left gripper, then confirm possession before moving toward the box; no human intervention is needed.
- Severity: low
- Severity evidence: The consequence is another unsuccessful pickup, with no visible damage or meaningful risk of damage.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the work surface and the environment requires no intervention for another attempt.