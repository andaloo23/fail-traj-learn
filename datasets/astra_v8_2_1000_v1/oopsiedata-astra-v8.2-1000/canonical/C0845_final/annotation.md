# Episode: C0845

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed throughout the episode, including frames 0, 120, 240 and 399 in image and left_ego_image. The robot approaches the upper front of the oven but then hovers with small repeated movements without opening it. wrist_image at frames 61, 200 and 399 shows the fingers beside the oven rather than visibly securing its handle. This is observed noncompletion with sustained unproductive behavior, not merely an action whose completion falls outside the recording.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 62 | No |
| 62 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 62-400
- Categories: task_not_attempted
- Explanation: After the initial approach, the robot remains near the oven with prolonged pauses and small back-and-forth movements, without discernible progress toward handle acquisition or door opening. Frames 62–114, 138–179 and 270–399 in image and left_ego_image show this sustained lack of progress; wrist_image at frames 100, 200 and 399 provides no evidence of a secured handle. The door stays closed. The visible failure is stalling, not an established failed grasp or hardware malfunction.
- Recovery: Re-localize the oven handle, reposition the open fingers to straddle it, establish a secure grasp, and pull along the door’s opening path while monitoring motion and clearance. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains unfinished, but no damage, displaced objects or meaningful damage risk is visible in image or left_ego_image through frame 399.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; another approach can be attempted without environmental resetting or human intervention.