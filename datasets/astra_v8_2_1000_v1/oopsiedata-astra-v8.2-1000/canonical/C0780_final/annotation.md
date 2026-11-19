# Episode: C0780

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image, the green can reaches the upper tray by frame 1100, but the blue bowl is subsequently placed in that same tray rather than the right tray (frames 2143–2449). During bowl acquisition, the gripper also displaces the nearby pink-and-yellow can (frames 1500–1748). The robot later places that can inside the misplaced bowl in the upper tray (frame 3400). At frame 3653, the right tray remains empty and the pink bowl remains on the table beneath the gripper. Thus there is a confirmed wrong-destination placement as well as unfinished work; the final bowl acquisition is unconfirmed, not an established failed grasp or abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1600 | No |
| 1600 | 1748 | Yes |
| 1748 | 2143 | No |
| 2143 | 2450 | Yes |
| 2450 | 3654 | No |

## Failure annotations

### Failure 1

- Frames: 1600-1748
- Categories: collision
- Explanation: While acquiring the blue bowl, the gripper contacts and displaces the adjacent pink-and-yellow can: in base_image it changes from its near-horizontal position at frame 1500 to a diagonal position beside the gripper at frames 1600–1700. By frame 1748, the bowl and gripper have lifted clear, leaving the displaced can on the table. This is unintended disturbance of another object, despite successful bowl acquisition; the exact contact onset between the sampled frames is uncertain.
- Recovery: Continue carrying the bowl with clearance from nearby objects, then reacquire the displaced can at its updated position for placement in the upper tray. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The can remains on the tabletop and accessible at frame 1748; no damage, spill, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The displaced can can be acquired directly from its new position without repair or human resetting.

### Failure 2

- Frames: 2143-2450
- Categories: sequencing_semantic
- Explanation: In base_image frames 2143–2400, the robot lowers the blue bowl into the upper tray, and frames 2448–2450 show withdrawal leaving the bowl there instead of in the right tray. This is a wrong-destination placement, not a failed acquisition. The preceding overhead transport is less conclusive about destination; the lowering and release establish the semantic failure. Subsequent movement toward the remaining can advances the task and is not an extension of this failure.
- Recovery: Remove the can subsequently placed inside the blue bowl and set it directly in the upper tray, then securely reacquire the bowl and transfer it to the right tray. Finish transferring the pink bowl to the right tray. No human intervention is visibly required.
- Severity: low
- Severity evidence: The misplaced bowl remains upright and accessible, including after the can is placed inside it at frame 3400; no breakage, spill, or other damage is visible.
- Resetability: immediate
- Resetability evidence: The objects remain reachable and can be rearranged through ordinary pick-and-place actions; the later nested can requires an additional move but no environmental repair or human reset.