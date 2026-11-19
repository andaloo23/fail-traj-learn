# Episode: C0388

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: success but suboptimal
- Outcome evidence: In base_image, an initial can acquisition fails: the gripper lifts away empty at frames 64–72 while both cans remain on the table, then travels to the upper tray. Subsequent handling succeeds: the green can is in the upper blue tray by frame 162, both cans are there by frame 241, and the blue bowl is released in the right red tray by frame 312. The pink bowl is subsequently nested with the blue bowl, and frames 400–424 show both cans in the upper tray and both bowls in the right tray with the robot withdrawn. No damage or unrelated side effect is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 64 | No |
| 64 | 105 | Yes |
| 105 | 425 | No |

## Failure annotations

### Failure 1

- Frames: 64-105
- Categories: grasp
- Explanation: Following closure near the pink-labeled can in base_image frames 53–63, the gripper begins lifting away at frame 64 without acquiring it; frames 67–72 show both cans still on the table. The empty gripper continues to the upper blue tray and performs an unproductive placement-like motion through frame 104. This does not transfer a can or advance the sorting task.
- Recovery: Return to a can, align the fingers around its body, close securely, and verify that it moves with the gripper before transporting it to the upper tray; no human intervention is needed.
- Severity: low
- Severity evidence: The failed acquisition leaves the cans on the tabletop; no damage, spill, or meaningful damage risk is visible in base_image frames 64–104.
- Resetability: immediate
- Resetability evidence: Both cans remain accessible on the table, so another acquisition can be attempted without human intervention or an environmental reset.