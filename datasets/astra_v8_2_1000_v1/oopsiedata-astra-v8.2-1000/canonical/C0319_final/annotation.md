# Episode: C0319

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image frames 800–1000, the green can is transferred to the upper tray, but frames 1226–1282 show the pink can slipping away during its transfer. Later, frames 2300–2494 show the blue bowl moved into the upper tray rather than the right tray. At frame 2615, the blue bowl remains in the upper tray, the pink bowl remains on the table, and the right tray is empty. Thus the requested sorting visibly fails, rather than completion merely being unconfirmed. The recording ending does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1226 | No |
| 1226 | 1283 | Yes |
| 1283 | 1639 | No |
| 1639 | 1722 | Yes |
| 1722 | 2255 | No |
| 2255 | 2494 | Yes |
| 2494 | 2616 | No |

## Failure annotations

### Failure 1

- Frames: 1226-1283
- Categories: grasp
- Explanation: In base_image frames 1226–1227, the pink can rotates downward away from the lifting gripper; by frames 1281–1282, it has settled outside the upper tray beside the blue bowl while the gripper withdraws without it. This establishes unsuccessful retention during transfer; the underlying cause is not visible.
- Recovery: Re-localize the pink can and acquire it individually with clearance from the bowl and tray, then verify retention before moving it fully over the upper tray. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The can remains on the tabletop with no visible spill or newly established damage; its crushed appearance was already present at frame 0.
- Resetability: immediate
- Resetability evidence: The displaced can remains accessible for another approach without environmental restoration or human intervention.

### Failure 2

- Frames: 1639-1722
- Categories: collision
- Explanation: During the crowded can interaction in base_image frames 1639–1721, the upper tray shifts and rotates and the adjacent blue bowl shifts left, as confirmed by comparison with frame 1700. These unintended displacements disrupt the arrangement rather than sorting the objects. The exact contact chain is occluded; upward withdrawal begins around frame 1722.
- Recovery: Clear the tray rim and bowl, re-localize the displaced objects, and approach an individual can with adequate clearance before transferring it. No human intervention is visibly required.
- Severity: low
- Severity evidence: The tray and bowl remain upright on the table, with no visible spill, breakage, or meaningful damage risk established.
- Resetability: immediate
- Resetability evidence: The objects remain accessible and can be handled at their updated positions; restoring the tray's exact original pose is unnecessary for another attempt.

### Failure 3

- Frames: 2255-2494
- Categories: sequencing_semantic
- Explanation: Beginning around base_image frame 2255 and clearly visible by frame 2300, the robot moves the blue bowl together with the adjacent can toward the upper tray. Frames 2400–2493 show the bowl being left there, and frames 2494–2615 confirm that it remains in this incorrect destination. This is one continuous incorrect-sorting action; the partly occluded grip does not independently establish a grasp failure.
- Recovery: Reacquire the blue bowl individually and place it in the right tray, then transfer the pink bowl there as well and verify that both cans are contained in the upper tray. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The observed consequence is incorrect sorting, with no visible spill, breakage, or newly established damage.
- Resetability: immediate
- Resetability evidence: The misplaced bowl remains accessible in the upper tray and can be directly reacquired for corrective sorting without a human reset.