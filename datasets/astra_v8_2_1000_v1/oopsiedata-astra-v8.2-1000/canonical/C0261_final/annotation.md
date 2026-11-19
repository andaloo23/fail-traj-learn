# Episode: C0261

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: The robot places the carrot and brown food-shaped object in the green bowl (wrist_cam, frames 223 and 817) and both plush toys in the lavender bowl (wrist_cam, frame 580). However, the orange fruit-shaped object leaves the gripper before reaching the green bowl and lands on the table (overhead_cam and wrist_cam, frames 987–998). It remains outside both bowls at frame 1130; this is a visibly failed final transfer, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 987 | No |
| 987 | 1054 | Yes |
| 1054 | 1131 | No |

## Failure annotations

### Failure 1

- Frames: 987-1054
- Categories: grasp
- Explanation: After successfully carrying the orange fruit-shaped object, the robot loses it before placement: wrist_cam shows it separating from the fingers at frames 987–989, and both cameras show it landing and rolling outside the green bowl at frames 990–1006. The empty gripper subsequently continues toward the bowl and opens there at frames 1045–1053 rather than retrieving the object. The images establish failed retention/placement, but not the underlying cause of release.
- Recovery: Locate the orange object on the tabletop, reacquire it, verify retention, and carry it over the green bowl before releasing at low height; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The object falls onto and remains on the tabletop; no damage, spill, or meaningful damage risk is visible in either camera.
- Resetability: immediate
- Resetability evidence: The orange object remains accessible on the table, and both bowls remain upright with their previously sorted contents; another acquisition can be attempted without environmental intervention.