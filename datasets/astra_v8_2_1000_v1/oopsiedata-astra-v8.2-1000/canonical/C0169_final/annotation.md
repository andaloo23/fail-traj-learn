# Episode: C0169

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The spoon remains on the tabletop outside the open drawer from frame 0 through frame 101 in image and left_ego_image. The robot repositions its empty gripper, then hovers with small adjustments without acquiring the spoon; wrist_image likewise shows no spoon possession. Placement is not completed, and the late sustained lack of progress is visible; no completed failed grasp or abnormal interruption is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 53 | No |
| 53 | 102 | Yes |

## Failure annotations

### Failure 1

- Frames: 53-102
- Categories: task_not_attempted
- Explanation: After the initial repositioning, the robot remains in approximately the same hovering configuration with only small adjustments during frames 53–101 in image and left_ego_image. The spoon stays untouched on the table, and wrist_image shows the empty gripper without an acquisition attempt. This sustained interval makes no visible progress toward putting the spoon in the drawer; the underlying cause is not visible.
- Recovery: Locate the spoon, approach and align the gripper for acquisition, verify a secure grasp, then transfer and release it inside the open drawer. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The task remains incomplete, but frames 53–101 show no damage, displaced objects, or concrete risk of damage.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop and the drawer remains open; no environmental restoration or human reset is visibly required.