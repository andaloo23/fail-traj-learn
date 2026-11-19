# Episode: C0804

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. The robot approaches the oven during frames 1–108, but no closing rotation is visible. After settling near the opening, it remains stationary for most of the episode; frames 140, 250 and 399 in left_ego_image show the door still lowered and open, corroborated by image and wrist_image. The task is visibly incomplete, with sustained stalling rather than merely an unconfirmed final closure.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 140 | No |
| 140 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 140-400
- Categories: task_not_attempted
- Explanation: Following the approach, the robot remains essentially stationary near the oven for approximately 22 seconds without moving the door toward closed. Frames 140, 200, 300 and 399 in image and left_ego_image show the unchanged open door and robot pose; wrist_image likewise shows the fingers remaining near the yellow plate and door area. This sustained lack of progress establishes stalling, but does not establish a grasp failure or mechanical cause.
- Recovery: Reassess the door and handle positions, move to a suitable contact pose, and lift the door along its hinge arc until closed, then verify closure. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The oven remains open, but no damage, displaced scene objects or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The scene remains intact with the door accessible; another closing attempt requires no visible environmental reset or human intervention.