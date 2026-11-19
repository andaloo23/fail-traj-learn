# Episode: C0359

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: In left_ego_image and image, the door moves slightly outward around frames 78–82 and more clearly opens partway at frames 130–137, but returns closed by frames 143–148. It remains closed through frame 399 while the robot stays near the handle. This is a visibly unsuccessful opening attempt, not merely unconfirmed completion; no damage or unrelated object displacement is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 83 | No |
| 83 | 94 | Yes |
| 94 | 138 | No |
| 138 | 148 | Yes |
| 148 | 173 | No |
| 173 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 83-94
- Categories: manipulation
- Explanation: After the door moves slightly outward at frames 78–82, it moves back toward its closed position during frames 83–93 in left_ego_image and image, undoing the initial opening progress. The images do not establish whether this results from slipping or the robot's motion.
- Recovery: Re-establish a secure handle engagement and pull outward and downward along the door's hinge arc, checking that the opening increases; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The opening progress is lost, but no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven remains upright and accessible, with no environmental reset needed before another attempt.

### Failure 2

- Frames: 138-148
- Categories: manipulation
- Explanation: left_ego_image and image show the door partially open at frames 132–137, then returning upward and inward during frames 138–147 rather than continuing to open. The robot does not preserve the achieved opening; the precise contact or retention cause is unclear.
- Recovery: Secure the handle again and maintain controlled engagement through the full opening arc before releasing; no human intervention is visibly required.
- Severity: low
- Severity evidence: The door closes again without visible damage, displaced surroundings, or other harmful consequences.
- Resetability: immediate
- Resetability evidence: The closed door and handle remain available for an immediate retry without scene restoration.

### Failure 3

- Frames: 173-400
- Categories: task_not_attempted
- Explanation: Following the small repositioning movements through approximately frame 172, the robot remains essentially stationary near the closed oven for the rest of the episode. Frames 173, 240, 320 and 399 in image, left_ego_image and wrist_image establish sustained lack of opening progress rather than a brief pause.
- Recovery: Resume a deliberate handle-alignment and opening attempt, verifying door movement rather than continuing to wait; no human intervention is indicated by the visible scene.
- Severity: low
- Severity evidence: The sustained stall leaves the task incomplete but causes no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: No objects require restoration, and the oven remains accessible for another attempt.