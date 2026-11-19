# Episode: C0277

## Episode annotation

- Language task: Pick up the red bowl and place it in the grey bowl.
- Success label: failure
- Outcome evidence: The red bowl is never placed in the grey bowl. The right and wrist views show repeated unsuccessful acquisitions at frames 65–97, 169–201 and 377–393, followed by a successful lift at frames 433–441. During subsequent transport, the grey bowl is displaced toward the counter edge and tips onto the adjacent robot-side surface (right, frames 462–513). The robot ultimately sets the red bowl back on the counter separately from the grey bowl and withdraws empty (right and wrist, frames 577–599); this is a visibly unsuccessful outcome, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 87 | No |
| 87 | 93 | Yes |
| 93 | 169 | No |
| 169 | 193 | Yes |
| 193 | 230 | No |
| 230 | 329 | Yes |
| 329 | 385 | No |
| 385 | 393 | Yes |
| 393 | 462 | No |
| 462 | 513 | Yes |
| 513 | 585 | Yes |
| 585 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 87-93
- Categories: grasp
- Explanation: After closing on the red bowl's rim and moving it, the gripper separates from the bowl at frames 87–89; the bowl remains on the counter while the closed fingers move away (right and wrist, frames 87–92). The acquisition is not retained.
- Recovery: Reopen, realign around the rim, and verify a secure grip with a small lift before transport; no human intervention is needed.
- Severity: low
- Severity evidence: The bowl remains upright on the counter without visible damage or spilling.
- Resetability: immediate
- Resetability evidence: The red bowl remains accessible for another grasp without environmental intervention.

### Failure 2

- Frames: 169-193
- Categories: grasp
- Explanation: The second closure shifts and rocks the red bowl rather than securely acquiring it (right and wrist, frames 169–175). It remains on the counter through frame 192, and the fingers reopen at frame 193 without having lifted it.
- Recovery: Adjust the finger placement and approach angle to capture the rim securely, then test retention before moving laterally; no human intervention is needed.
- Severity: low
- Severity evidence: Only the acquisition fails; no damage or hazardous displacement is visible.
- Resetability: immediate
- Resetability evidence: The bowl is still upright and within reach on the counter.

### Failure 3

- Frames: 230-329
- Categories: task_not_attempted
- Explanation: Following the second retry's withdrawal, the empty gripper remains away from the red bowl for a sustained interval, with nearly unchanged poses at frames 230–291 and further empty repositioning at frames 292–328 (right and wrist). Neither bowl is advanced toward the requested nesting during this interval; a renewed approach begins at frame 329.
- Recovery: Resume a targeted approach to the red bowl using its current position rather than continuing to hover or reposition empty; no human intervention is visibly required.
- Severity: low
- Severity evidence: The consequence is delay, with no visible damage during this interval.
- Resetability: immediate
- Resetability evidence: Both bowls remain available and no scene reset is necessary.

### Failure 4

- Frames: 385-393
- Categories: grasp
- Explanation: Following another rim closure, the fingers close beside the red bowl and separate from it while the bowl stays on the counter (wrist and right, frames 385–392). The gripper then opens and repositions at frame 393.
- Recovery: Reposition the open fingers across the rim and confirm possession before withdrawing; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition produces no visible damage, spilling or overturning.
- Resetability: immediate
- Resetability evidence: The red bowl remains upright and accessible for an immediate retry.

### Failure 5

- Frames: 462-513
- Categories: collision
- Explanation: While the red bowl is held, the grey bowl begins sliding toward the counter edge alongside the moving robot and its hanging cable (right, frames 462–505). It tips over the edge at frames 507–510 and settles on the adjacent robot-side surface by frame 513. This unintended displacement disrupts the receiving location; the precise contact point is partly obscured.
- Recovery: Stop transport, put the held red bowl safely on a clear surface, and have a person restore the grey bowl to a stable counter position after checking cable clearance.
- Severity: medium
- Severity evidence: The grey bowl is pushed to and over the counter edge, creating a concrete impact risk and disrupting the task setup; no actual breakage is visible.
- Resetability: minor_reset
- Resetability evidence: The grey bowl remains visible near the robot and appears retrievable with a straightforward manual repositioning, rather than repair or extensive retrieval.

### Failure 6

- Frames: 513-585
- Categories: sequencing_semantic
- Explanation: With the red bowl securely held, the robot carries it away from the displaced grey bowl toward the sink-side counter, lowers it there, and releases it outside the receiving bowl (right and wrist, frames 513–577). By frame 585 the empty gripper is separated from the red bowl. This completes the wrong placement rather than the requested nesting.
- Recovery: Once the grey bowl has been safely restored, reacquire the red bowl and place it centrally inside the grey bowl, verifying support before release; human intervention is needed for the preceding grey-bowl displacement, not for this placement alone.
- Severity: low
- Severity evidence: The red bowl is left upright on the counter without visible damage; the consequence of this segment is incorrect placement.
- Resetability: immediate
- Resetability evidence: This segment leaves the red bowl accessible for reacquisition and adds no reset requirement beyond the separate grey-bowl displacement.