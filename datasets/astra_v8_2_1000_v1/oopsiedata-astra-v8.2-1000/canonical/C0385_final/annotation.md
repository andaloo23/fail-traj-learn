# Episode: C0385

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. After approaching the door, the robot spends a prolonged interval near its handle without closing it, then makes further arm adjustments. At frames 320 and 350, image still shows the door projecting outward rather than shut; wrist_image also shows its exposed inner surface. Closure is not achieved in the observed episode, although the final interaction may be unfinished.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 43 | No |
| 43 | 250 | Yes |
| 250 | 351 | No |

## Failure annotations

### Failure 1

- Frames: 43-250
- Categories: task_not_attempted
- Explanation: Following the approach, the robot remains nearly stationary at the open door with only small adjustments for roughly 17 seconds. Frames 43, 100, 150, 200 and 249 in image and left_ego_image show no sustained closing progress; wrist_image likewise shows little change in the door–gripper relationship. This is sustained unproductive stalling, not absence of an initial task attempt. The images do not establish a failed grasp or a mechanical cause.
- Recovery: Reassess the handle and hinge geometry, establish a secure contact, and guide the door upward along its closing arc while monitoring clearance and resistance. No human intervention is visibly required; stop and request inspection if the door resists rather than forcing it.
- Severity: low
- Severity evidence: The door remains open, but no damage, displaced unrelated objects or meaningful damage risk is visible during this interval.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain available for another attempt; no environmental cleanup or human reset is visibly needed.