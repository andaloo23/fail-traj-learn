# Episode: C0698

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. The robot approaches the door during frames 8–46 and makes small positional adjustments afterward, but the door remains lowered at frames 79, 120 and 178 in image and left_ego_image. Completion is visibly not achieved; the extended near-stationary behavior establishes a local stall, although wrist_image does not establish a secure grasp or a mechanical cause.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 79 | No |
| 79 | 179 | Yes |

## Failure annotations

### Failure 1

- Frames: 79-179
- Categories: task_not_attempted
- Explanation: After approaching and adjusting near the open door, the robot remains in essentially the same pose from frame 79 through frame 178, with only small movements and no visible door-closing progress. image and left_ego_image show the door remaining lowered at frames 79, 120 and 178; wrist_image shows the gripper remaining near the door without establishing successful acquisition. This is sustained stalling rather than a brief alignment pause.
- Recovery: Reassess the door handle and gripper alignment, establish controlled contact, and lift the door along its hinge arc until closed, verifying closure visually. No human intervention is visibly required; if resistance prevents movement, stop and inspect rather than forcing the door.
- Severity: low
- Severity evidence: The oven remains open, but no damage, displaced unrelated objects or meaningful damage risk is visible in image or left_ego_image through frame 178.
- Resetability: immediate
- Resetability evidence: The door and surrounding scene remain available for another attempt; no environmental restoration or human reset is visibly needed.