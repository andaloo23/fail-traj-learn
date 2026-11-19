# Episode: C0774

## Episode annotation

- Language task: Open the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven starts closed in frame 0, left_ego_image. After approaching its handle, the robot remains nearly stationary for a sustained interval around frames 60–100 in image, left_ego_image and wrist_image. It subsequently pulls the door downward; frames 150–166 in image and left_ego_image show the open door and exposed oven interior. No damage or disturbance of unrelated objects is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 60 | No |
| 60 | 101 | Yes |
| 101 | 167 | No |

## Failure annotations

### Failure 1

- Frames: 60-101
- Categories: task_not_attempted
- Explanation: Following the approach, the robot sustains a nearly unchanged position beside the oven handle without visibly opening the door during frames 60–100 in image, left_ego_image and wrist_image. This prolonged pause does not advance the task; its underlying cause is not visible.
- Recovery: Resume task-directed handle alignment and acquisition, then pull the door along its hinge trajectory while monitoring clearance; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is delay only; the oven and surrounding objects remain intact and undisturbed.
- Resetability: immediate
- Resetability evidence: No environmental change requires resetting, so the robot can continue from its current position without human intervention.