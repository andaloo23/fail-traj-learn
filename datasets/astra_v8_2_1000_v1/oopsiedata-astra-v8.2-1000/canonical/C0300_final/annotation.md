# Episode: C0300

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 and remains visibly open at frame 300 in left_ego_image, corroborated by image. The robot approaches the door, spends a prolonged interval nearly stationary beside it, and makes later small adjustments without completing closure. This is a visibly unmet task, not merely an occluded final outcome; the images do not establish a completed failed grasp or abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 90 | No |
| 90 | 198 | Yes |
| 198 | 301 | No |

## Failure annotations

### Failure 1

- Frames: 90-198
- Categories: task_not_attempted
- Explanation: After approaching and aligning beside the open door, the robot remains essentially stationary without advancing closure for roughly nine seconds. Frames 90, 120, 160, and 197 in image and left_ego_image show the same gripper placement and open door; wrist_image likewise shows no meaningful change in the gripper–door relationship. This sustained stall is distinct from the preceding approach and subsequent renewed adjustments; its underlying cause is not visible.
- Recovery: Reassess the handle and door geometry, establish a suitable grasp or supported contact, and move the door upward along its hinge arc while monitoring clearance and closure. No human intervention is visibly required.
- Severity: low
- Severity evidence: The stall leaves the task unfinished, but no damage, displaced unrelated objects, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven remains open and the surrounding scene remains intact; another task-directed attempt requires no environmental reset or human intervention.