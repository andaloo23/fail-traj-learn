# Episode: C0367

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the cardboard box.
- Success label: failure
- Outcome evidence: The stuffed animal remains on the tabletop outside the box throughout the episode. The external and wrist views show closed, empty gripper withdrawals at frames 344, 548, and 822 after acquisition attempts. At frame 1274, external shows the animal still on the table and wrist shows the gripper near its head, without a confirmed grasp or placement. Thus earlier attempts visibly failed; the final approach has an unconfirmed outcome rather than a demonstrated completed acquisition.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 332 | No |
| 332 | 428 | Yes |
| 428 | 543 | No |
| 543 | 627 | Yes |
| 627 | 818 | No |
| 818 | 907 | Yes |
| 907 | 1275 | No |

## Failure annotations

### Failure 1

- Frames: 332-428
- Categories: grasp
- Explanation: Following finger closure near the animal's lower body at frames 327-331 in wrist, the robot withdraws empty beginning at frame 332. By frames 344-346, external shows clear separation while the animal remains on the table, and wrist shows the closed fingers without the animal. The robot remains in this unsuccessful state until the renewed approach at frame 428.
- Recovery: Reopen the fingers, realign them around a substantial portion of the animal's torso, and verify retention with a small test lift before transport; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The animal stays on the table; neither camera shows damage or harmful displacement.
- Resetability: immediate
- Resetability evidence: The target and box remain accessible in their original workspace, so another acquisition can be attempted without environmental intervention.

### Failure 2

- Frames: 543-627
- Categories: grasp
- Explanation: After another closure at frames 537-542 in wrist, the gripper lifts away without retaining the animal beginning at frame 543. Frames 548-551 in external show the empty gripper above the unchanged target; wrist likewise shows the animal separated from the closed fingers. The subsequent empty withdrawal ends when renewed alignment begins at frame 627.
- Recovery: Open the gripper and revise the grasp location and descent depth so both fingers surround the torso rather than close near its edge; confirm a secure low lift before moving toward the box. Human intervention is not required by the visible state.
- Severity: low
- Severity evidence: Only acquisition is prevented; no damage, falling object, or disturbance of the box is visible.
- Resetability: immediate
- Resetability evidence: The animal remains safely on the tabletop and available for an immediate revised attempt.

### Failure 3

- Frames: 818-907
- Categories: grasp
- Explanation: Closure near frames 810-813 produces a brief tug or deformation during frames 814-817, but at frame 818 the gripper separates empty. External frames 822 and 904 show the animal still on the table as the arm withdraws; wrist confirms no retained animal between the fingers. A new approach begins at frame 907.
- Recovery: Reopen and reposition for a deeper, centered torso grasp, using a short verification lift to check retention before transport. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The soft animal settles on the table without visible damage, and no unrelated objects are disturbed.
- Resetability: immediate
- Resetability evidence: No cleanup or object retrieval is necessary; the animal and box remain usable and reachable for another attempt.
