# Episode: C0870

## Episode annotation

- Language task: Pick up the ball and place it in the bowl.
- Success label: failure
- Outcome evidence: The orange ball remains outside the blue bowl throughout the episode. camera_high and camera_wrist_right show repeated empty withdrawals after acquisition attempts, including frames 174–205 and 378–405. At frames 738–749, camera_wrist_left shows the gripper above the ball while it remains on the table; camera_high confirms the bowl is still empty. This is a visibly unsuccessful pickup sequence, not merely unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 174 | No |
| 174 | 206 | Yes |
| 206 | 378 | No |
| 378 | 406 | Yes |
| 406 | 491 | No |
| 491 | 507 | Yes |
| 507 | 730 | No |
| 730 | 750 | Yes |

## Failure annotations

### Failure 1

- Frames: 174-206
- Categories: grasp
- Explanation: The gripper withdraws from the acquisition position without the ball. camera_high shows the orange ball remaining on the table at frames 174–205 while the gripper moves away toward the bowl; camera_wrist_right shows empty fingers by frames 190–205. The attempted pickup did not establish retention.
- Recovery: Reopen and realign the fingers around opposite sides of the ball, then close and verify possession with a small lift before transferring it; no human intervention is needed.
- Severity: low
- Severity evidence: The ball remains on the tabletop and no damage or harmful disturbance is visible.
- Resetability: immediate
- Resetability evidence: The ball and bowl remain accessible in a valid state for another attempt without environmental resetting.

### Failure 2

- Frames: 378-406
- Categories: grasp
- Explanation: Following another approach and closing attempt, the gripper rises empty at frames 378–405. camera_wrist_left shows the fingers separating vertically from the ball, and camera_high confirms that the ball stays outside the bowl on the table.
- Recovery: Lower with an adjusted grasp alignment, enclose the ball between both fingers, and confirm that it follows the gripper during a short test lift; no human intervention is needed.
- Severity: low
- Severity evidence: This attempt only prevents task completion; no damage is visible.
- Resetability: immediate
- Resetability evidence: The target remains on the usable tabletop and can be approached again directly.

### Failure 3

- Frames: 491-507
- Categories: grasp
- Explanation: The next withdrawal again leaves the ball behind. At frames 491–506, camera_wrist_left shows empty fingers lifting above the stationary orange ball, while camera_high shows no transfer into the bowl.
- Recovery: Reassess the ball's position relative to both fingertips and adjust the acquisition pose rather than repeating the same miss; verify a secure pickup before moving to the bowl. Human intervention is not required.
- Severity: low
- Severity evidence: The visible consequence is another failed pickup, with no observed damage or significant displacement.
- Resetability: immediate
- Resetability evidence: Neither the ball nor the bowl requires repositioning or repair for another attempt.

### Failure 4

- Frames: 730-750
- Categories: grasp
- Explanation: After the final closing attempt, the gripper lifts away without the ball at frames 730–749. camera_wrist_left clearly shows a gap between the raised fingers and the ball by frames 738–749; camera_high confirms the ball remains on the table outside the bowl.
- Recovery: Reopen, correct the fingertip alignment and acquisition height, and perform a verified test lift before attempting placement; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The ball is left on the tabletop without visible damage; no additional harmful consequence is established.
- Resetability: immediate
- Resetability evidence: The scene remains usable and the ball is accessible for a new grasp without a human reset.