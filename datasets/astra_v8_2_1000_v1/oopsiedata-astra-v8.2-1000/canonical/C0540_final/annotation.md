# Episode: C0540

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in left_ego_image and remains open at frames 76 and 234. The robot repositions near the oven during frames 0–75 but never visibly raises or closes the door; image and wrist_image also show no successful door movement. It then remains essentially stationary through frame 234. Thus the task is visibly incomplete, with sustained inactivity rather than an established failed door grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 76 | No |
| 76 | 235 | Yes |

## Failure annotations

### Failure 1

- Frames: 76-235
- Categories: task_not_attempted
- Explanation: After the initial repositioning, the gripper remains essentially stationary above the tabletop near the green plate while the oven door stays open; compare frames 76, 120, 180 and 234 in image, left_ego_image and wrist_image. This sustained interval of roughly 13 seconds makes no visible progress toward closing the oven. No hardware malfunction or abnormal termination is established.
- Recovery: Locate the open door and its handle, approach with clearance from the dishes, and lift the door along its hinge motion until closed, then verify closure. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible during the stationary interval.
- Resetability: immediate
- Resetability evidence: The oven remains open and the surrounding objects remain in place, so another attempt can begin without an environmental reset or human intervention.