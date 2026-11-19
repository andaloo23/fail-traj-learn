# Episode: C0593

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains upright and closed in left_ego_image at frames 0, 108, 200 and 315, corroborated by image. The robot approaches the upper door/handle area but never visibly opens the door. Frames 108–315 show prolonged hovering with only small positional changes rather than an opening action; wrist_image does not establish a secure handle grasp. This is visible noncompletion with sustained unproductive behavior, not merely an action cut off before its outcome.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 108 | No |
| 108 | 316 | Yes |

## Failure annotations

### Failure 1

- Frames: 108-316
- Categories: task_not_attempted
- Explanation: After approaching and adjusting near the oven, the robot remains around the upper door/handle area without discernible opening progress for the rest of the episode. Frames 108, 150, 200, 250 and 315 in left_ego_image and image show the door unchanged; wrist_image shows only small viewpoint changes during this prolonged interval. The images support sustained stalling, but not a confirmed failed grasp, established handle control or a mechanical cause.
- Recovery: Re-localize the handle, align the fingers to acquire it securely, and then pull along the door’s opening arc while monitoring clearance and door movement. No human intervention is visibly required; stop and request assistance if a verified grasp and gentle pull encounter resistance.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced tabletop objects or meaningful damage risk is visible in image or left_ego_image through frame 315.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; the robot can reposition and reattempt without an environmental reset or visible need for human intervention.