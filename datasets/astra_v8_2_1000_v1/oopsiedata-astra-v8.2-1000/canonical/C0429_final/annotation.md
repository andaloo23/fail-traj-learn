# Episode: C0429

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot lifts the spoon toward the drawer twice, but it falls back onto the table at frames 139–145 and 260–264 (image, left_ego_image). A third acquisition also fails, with the gripper withdrawing while the spoon remains on the table at frames 361–399 (image, left_ego_image, wrist_image). The final visible spoon position is outside the drawer; this is a visibly failed task attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 139 | No |
| 139 | 146 | Yes |
| 146 | 260 | No |
| 260 | 266 | Yes |
| 266 | 353 | No |
| 353 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 139-146
- Categories: grasp
- Explanation: After carrying the spoon upward toward the drawer, the robot loses retention at frame 139; the spoon falls and settles on the tabletop by frames 144–145 rather than entering the drawer (image, left_ego_image). Whether this was slipping or premature release is unclear.
- Recovery: Locate the spoon again, acquire a more secure grasp, verify retention with a short lift, and position it fully over the drawer interior before releasing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The spoon falls onto the table with no visible breakage or meaningful damage.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop, allowing another attempt without environmental intervention.

### Failure 2

- Frames: 260-266
- Categories: grasp
- Explanation: Following a second successful lift, the spoon again separates from the gripper at frame 260 and falls onto the tabletop by frames 262–264 (image, left_ego_image). The transfer to the drawer is again interrupted by loss of retention.
- Recovery: Reacquire the spoon with a revised grasp and verify stable retention before transport; release only after confirming the spoon is inside the drawer opening. No human intervention is visibly required.
- Severity: low
- Severity evidence: The spoon lands on the usable tabletop without visible damage.
- Resetability: immediate
- Resetability evidence: The fallen spoon is still reachable and requires no human reset before retrying.

### Failure 3

- Frames: 353-400
- Categories: grasp
- Explanation: During the third acquisition, the spoon shifts out of the closing fingers around frames 353–360; the gripper then rises and moves away empty while the spoon stays on the table through frame 399 (image, left_ego_image, wrist_image). This completed acquisition attempt fails to retain the target, and the subsequent empty withdrawal does not advance placement.
- Recovery: Return to the spoon, realign the fingers around a secure grasp point, and confirm that the spoon follows a short test lift before moving toward the drawer; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The spoon remains on the tabletop, with no visible damage or substantial hazard from the failed acquisition.
- Resetability: immediate
- Resetability evidence: The target remains accessible in an otherwise usable scene, so another acquisition can be attempted without resetting the environment.