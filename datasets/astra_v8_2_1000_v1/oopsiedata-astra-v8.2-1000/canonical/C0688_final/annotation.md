# Episode: C0688

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in left_ego_image at frames 0, 98, 200 and 399. The robot initially moves toward the oven, but then remains essentially stationary above its front without opening it; wrist_image at frames 98–399 shows the fingers beside the oven rather than visibly pulling the handle. Completion is not observed, and sustained stalling is visible rather than merely an unfinished action at the recording end.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 98 | No |
| 98 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 98-400
- Categories: task_not_attempted
- Explanation: Following the initial approach, the gripper remains essentially fixed near the oven for approximately 25 seconds, with no discernible acquisition or opening movement (image, left_ego_image and wrist_image, frames 98, 150, 250 and 399). The door stays closed throughout this sustained unproductive interval; no hidden mechanical or planning cause is established.
- Recovery: Resume task-directed alignment with the oven handle, establish a secure grasp, and pull along the door’s opening trajectory while monitoring clearance; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced objects or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state, so another attempt requires no environmental reset or human intervention.