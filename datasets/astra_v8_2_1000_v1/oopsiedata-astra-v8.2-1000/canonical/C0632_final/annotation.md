# Episode: C0632

## Episode annotation

- Language task: Put the yellow toy pear into the blue bowl.
- Success label: failure
- Outcome evidence: The pear remains on the tabletop outside the bowl throughout the episode, including frame 240 in left_base_cam and right_base_cam. Approaches near the pear are followed by empty withdrawals at frames 68–98, 163–195, and 228–240; wrist_cam also shows the pear remaining on the table. These establish unsuccessful acquisition attempts, rather than merely unconfirmed placement. No successful lift or placement is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 68 | No |
| 68 | 99 | Yes |
| 99 | 163 | No |
| 163 | 196 | Yes |
| 196 | 228 | No |
| 228 | 241 | Yes |

## Failure annotations

### Failure 1

- Frames: 68-99
- Categories: grasp
- Explanation: Following the close approach at frames 60–67, the gripper withdraws without the pear during frames 68–98. left_base_cam and right_base_cam show the pear remaining beside the bowl, while wrist_cam shows increasing separation from the target. The near-object acquisition attempt therefore fails; the precise contact mechanics are not clear.
- Recovery: Reopen the gripper, align the fingers on opposite sides of the pear, descend to an appropriate grasp height, and verify acquisition with a small lift before moving toward the bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The pear stays on the tabletop, and no damage, spill, or disruptive object displacement is visible.
- Resetability: immediate
- Resetability evidence: The pear and bowl remain accessible in their original working area; no environmental reset or human intervention is needed.

### Failure 2

- Frames: 163-196
- Categories: grasp
- Explanation: After another approach close to the pear at frames 153–162, the gripper again moves upward and away empty during frames 163–195. The stationary pear is visible in left_base_cam and right_base_cam, with wrist_cam confirming that it remains on the table rather than traveling with the gripper.
- Recovery: Correct the grasp alignment and height using the visible pear position, close around its body, and verify a secure lift before transport; no human intervention is visibly required.
- Severity: low
- Severity evidence: This attempt leaves the task incomplete without visible damage or meaningful disturbance to the scene.
- Resetability: immediate
- Resetability evidence: Both task objects remain available on the table, allowing another attempt without resetting the environment.

### Failure 3

- Frames: 228-241
- Categories: grasp
- Explanation: The third close approach at frames 219–227 is followed by an empty withdrawal beginning at frame 228. By frames 238–240, left_base_cam and right_base_cam show the gripper separated from the pear, which remains outside the bowl; wrist_cam likewise shows the pear on the tabletop. This is another failed acquisition, not evidence of a drop or abnormal termination.
- Recovery: Reposition the open fingers to straddle the pear at grasp height and confirm that the pear lifts with the gripper before attempting placement; no human intervention is visibly needed.
- Severity: low
- Severity evidence: No object damage or harmful side effect is visible; the consequence is failure to acquire and place the pear.
- Resetability: immediate
- Resetability evidence: The pear remains accessible beside the upright bowl, with no cleanup or object restoration needed.