# Episode: C0274

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in left_ego_image. The robot moves toward its front during frames 76–102 in image and left_ego_image, but the door remains lowered at frames 103 and 153 in left_ego_image. The final interval shows sustained inactivity rather than visible closure; no completed failed grasp or established door control is evident.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 103 | No |
| 103 | 154 | Yes |

## Failure annotations

### Failure 1

- Frames: 103-154
- Categories: task_not_attempted
- Explanation: After approaching the oven, the robot remains essentially stationary beside its front from frame 103 through frame 153 in image and left_ego_image. The door stays lowered throughout this roughly four-second interval, with no discernible closing progress. Small wrist_image changes do not establish door manipulation.
- Recovery: Reassess the door and handle position, establish suitable contact, and move the door along its hinge arc to closure while checking clearance; no human intervention is visibly required.
- Severity: low
- Severity evidence: The oven remains open, but no damage, displaced unrelated objects, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The scene remains usable with the door open; another closing attempt requires no visible environmental reset or human intervention.