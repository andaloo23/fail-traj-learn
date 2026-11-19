# Episode: C0077

## Episode annotation

- Language task: Open the drawer.
- Success label: success but suboptimal
- Outcome evidence: The upper drawer starts closed (frame 0, left_ego_image). An initial handle acquisition fails: the gripper withdraws without the handle and closes empty while the drawer stays shut (frames 101–117, wrist_image and left_ego_image). After repositioning, the robot pulls the upper drawer outward (frames 160–185, image and left_ego_image); it remains visibly open through frame 204. No unintended object displacement or damage is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 101 | No |
| 101 | 118 | Yes |
| 118 | 205 | No |

## Failure annotations

### Failure 1

- Frames: 101-118
- Categories: grasp
- Explanation: Following the initial approach around the upper drawer handle, the gripper moves away without acquiring it (frames 101–107, wrist_image). Its fingers subsequently close together clear of the handle (frames 108–117, wrist_image), while the drawer remains closed in left_ego_image. This establishes an unsuccessful acquisition rather than a successful pull.
- Recovery: Reopen the gripper, realign the fingers around the handle, secure the handle, and pull along the drawer’s sliding direction; no human intervention is needed.
- Severity: low
- Severity evidence: The attempt leaves the drawer closed, with no visible damage or disturbance to surrounding objects in image or left_ego_image.
- Resetability: immediate
- Resetability evidence: The cabinet and handle remain in place and accessible; the robot can reattempt acquisition without an environmental reset.