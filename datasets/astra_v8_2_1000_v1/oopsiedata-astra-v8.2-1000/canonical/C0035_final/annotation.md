# Episode: C0035

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: success but side effects
- Outcome evidence: In base_image, both cans are released into the upper blue tray by frames 523–529, and both bowls are stacked in the right red tray by frames 787–851. The initial green-can acquisition fails, followed by an empty trip to the upper tray (frames 127–211). During the later successful green-can transfer, contact displaces and rocks the blue bowl (frames 445–454); no damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 127 | No |
| 127 | 212 | Yes |
| 212 | 445 | No |
| 445 | 455 | Yes |
| 455 | 852 | No |

## Failure annotations

### Failure 1

- Frames: 127-212
- Categories: grasp
- Explanation: In base_image, the gripper withdraws after closing near the green can at frames 114–126, but the can remains on the table as the empty gripper rises at frames 127–140. The robot continues to the upper tray and opens without depositing anything at frames 143–211, so this acquisition and transfer do not advance the task.
- Recovery: Return to the green can, realign the fingers around its body, and verify that it moves with the gripper before transferring it; no human intervention is needed.
- Severity: low
- Severity evidence: The can remains accessible on the tabletop, with no visible new damage or spill; its crushed shape was already present at frame 0 in base_image.
- Resetability: immediate
- Resetability evidence: No environmental reset is needed because the missed can remains available for another grasp.

### Failure 2

- Frames: 445-455
- Categories: collision
- Explanation: In base_image, while lifting the acquired green can beside the blue bowl, the robot's carried object/gripper contacts the bowl, visibly shifting and rocking it across frames 445–454. This unintended movement is not the intended bowl transfer to the right tray; the exact contacting surface is partly obscured.
- Recovery: Lift the can clear of the bowl before translating toward the upper tray, then reacquire the bowl's updated position for its intended transfer; no human intervention is needed.
- Severity: low
- Severity evidence: The bowl rocks and shifts but remains on the table, with no visible breakage, contents spilled, or other damage.
- Resetability: immediate
- Resetability evidence: The displaced bowl remains accessible and usable, so the robot can continue from its updated position without a human reset.