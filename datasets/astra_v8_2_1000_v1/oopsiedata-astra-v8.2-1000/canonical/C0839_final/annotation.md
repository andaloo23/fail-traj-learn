# Episode: C0839

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains upright and closed in left_ego_image at frames 0, 46, 200 and 399. The robot initially moves toward the oven’s upper-front area, but then remains nearly stationary for most of the episode, as shown in image and wrist_image at frames 46–338. No door-opening motion is visible through frame 399; this is an observed failure to complete the task with sustained stalling, rather than merely an acquisition attempt cut off before its outcome.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 46 | No |
| 46 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 46-400
- Categories: task_not_attempted
- Explanation: After the initial positioning movement, the gripper stays near the oven’s upper-front area without visibly opening the door. Frames 46, 100, 200 and 338 in image, left_ego_image and wrist_image show sustained lack of task progress; slight subsequent movement through frame 399 also produces no opening. The views do not establish a secure handle grasp or a mechanical cause.
- Recovery: Reassess the handle position, align the gripper around it, verify acquisition, and pull along the door’s opening path while monitoring clearance and door movement. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced scene objects or concrete damage risk is visible in left_ego_image through frame 399.
- Resetability: immediate
- Resetability evidence: The oven remains closed and the surrounding scene remains intact; another handle-acquisition attempt can begin without an environmental reset or human intervention.