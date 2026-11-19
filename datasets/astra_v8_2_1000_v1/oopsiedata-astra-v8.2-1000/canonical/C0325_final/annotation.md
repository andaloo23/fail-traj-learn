# Episode: C0325

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the upper drawer handle, closes its gripper near it, and withdraws empty without opening the drawer (frames 69–123, wrist_image and left_ego_image). It subsequently remains away from the handle with only small movements and gripper cycling. The drawer is still closed at frame 324 in left_ego_image; this is a visibly unsuccessful attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 80 | No |
| 80 | 123 | Yes |
| 123 | 325 | Yes |

## Failure annotations

### Failure 1

- Frames: 80-123
- Categories: grasp
- Explanation: The fingers close beside the upper drawer handle starting at frame 80 in wrist_image, but do not retain it. At frames 91–123, wrist_image shows the closed, empty gripper separating from the handle, while left_ego_image shows the drawer remaining closed. The acquisition attempt therefore fails to enable a pull.
- Recovery: Reopen the gripper, realign the fingers around the handle with adequate clearance, verify acquisition, and then pull along the drawer’s sliding direction; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The drawer remains closed, with no visible damage or displacement of surrounding objects in image and left_ego_image.
- Resetability: immediate
- Resetability evidence: The handle remains accessible and the scene is unchanged; another aligned grasp can be attempted without an environmental reset.

### Failure 2

- Frames: 123-325
- Categories: task_not_attempted
- Explanation: After withdrawing, the robot stays away from the drawer handle from frame 123 through frame 324, with prolonged hovering, small movements away, and occasional empty gripper cycling (for example, frames 132–135 and 181–186, wrist_image). No renewed approach or drawer movement occurs in image or left_ego_image, establishing sustained unproductive behavior rather than a brief pause.
- Recovery: Resume a task-directed approach to the drawer handle and perform a verified grasp and controlled pull; no human intervention is visibly required.
- Severity: low
- Severity evidence: The consequence is lack of task progress; the cabinet and tabletop objects show no visible damage or disruption.
- Resetability: immediate
- Resetability evidence: The drawer remains closed and available for another attempt, with no cleanup, repositioning, or repair visibly necessary.