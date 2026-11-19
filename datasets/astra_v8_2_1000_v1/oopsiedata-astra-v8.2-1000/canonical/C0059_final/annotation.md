# Episode: C0059

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed at frame 0 in left_ego_image. The robot approaches its upper front area during frames 7–74 and makes small positional adjustments through frame 112, visible in image and wrist_image, but no door-opening motion occurs. Frames 113–399 show sustained inactivity with the door still closed in left_ego_image. The task is visibly unachieved; a secure handle grasp or failed pulling attempt is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 113 | No |
| 113 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 113-400
- Categories: task_not_attempted
- Explanation: After approaching the oven, the robot remains essentially stationary near its upper front area from frame 113 through frame 399, as seen in image and wrist_image. The door remains closed throughout in left_ego_image, so this sustained stall does not advance the task. The images do not establish handle possession or a mechanical cause.
- Recovery: Resume by locating the handle, aligning the gripper, establishing a secure grasp, and pulling along the door’s opening path while checking for door movement; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but frames 113–399 show no damage, displaced objects, or concrete risk of damage.
- Resetability: immediate
- Resetability evidence: The oven remains closed and the surrounding scene is unchanged; another attempt can begin without an environmental reset or human intervention.