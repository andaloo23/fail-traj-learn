# Episode: C0846

## Episode annotation

- Language task: Pick up the green bell pepper from the pink bowl and put it on the table.
- Success label: failure
- Outcome evidence: The pepper starts inside the bowl (frame 0, wrist_cam and right_base_cam). Three acquisition attempts end with the gripper withdrawing empty while the pepper remains in the bowl (frames 66, 137, and 193, wrist_cam and right_base_cam). At frame 240 it is still in the bowl, not on the table. The final repositioning is unfinished, but the earlier failed acquisitions are visibly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 60 | No |
| 60 | 81 | Yes |
| 81 | 133 | No |
| 133 | 142 | Yes |
| 142 | 185 | No |
| 185 | 201 | Yes |
| 201 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 60-81
- Categories: grasp
- Explanation: At frames 60-65, wrist_cam shows the fingers closing past the pepper without retaining it as the gripper rises; by frame 66, right_base_cam confirms an empty withdrawal with the pepper still in the bowl. The unsuccessful acquisition ends when reopening and realignment begin at frame 81.
- Recovery: Open the gripper, realign the fingers around the pepper's body at an appropriate depth, and verify retention with a small lift before transport; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The pepper remains contained in the upright bowl; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The target remains accessible in the bowl and another attempt requires no environmental reset.

### Failure 2

- Frames: 133-142
- Categories: grasp
- Explanation: Following a second closure, frames 133-137 in wrist_cam show the fingers separating from the pepper during an empty lift. right_base_cam at frame 137 confirms the pepper remains in the bowl. Reopening for another attempt begins at frame 142.
- Recovery: Reassess the pepper's position and grasp depth, reopen and reposition around its body, then verify a secure grasp before lifting farther; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The acquisition fails without visible damage, spillage, or displacement outside the bowl.
- Resetability: immediate
- Resetability evidence: The bowl remains upright and the pepper is available for an immediate retry without resetting the scene.

### Failure 3

- Frames: 185-201
- Categories: grasp
- Explanation: At frames 185-190, wrist_cam shows the fingers closed without retaining the pepper as the gripper withdraws. By frame 193, wrist_cam and right_base_cam clearly show the empty gripper above the bowl and the pepper still inside. The next reopening begins at frame 201.
- Recovery: Reopen and adjust the grasp position and depth rather than repeating the same unsuccessful closure; confirm possession with a short lift before moving toward a clear tabletop location. No human intervention is visibly required.
- Severity: low
- Severity evidence: Only acquisition is prevented; no visible damage or harmful side effect accompanies the empty withdrawal.
- Resetability: immediate
- Resetability evidence: The pepper remains accessible in the intact, upright bowl, so no human or environmental reset is needed.