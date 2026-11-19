# Episode: C0187

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in left_ego_image at frames 0, 48, 80 and 128. The robot moves toward the oven during the early frames, but then remains nearly stationary beside it without visible opening progress. image and wrist_image at frames 48–128 corroborate the lack of a door-opening motion. Completion is not observed; the visible local failure is sustained stalling, not an established failed handle grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 48 | No |
| 48 | 129 | Yes |

## Failure annotations

### Failure 1

- Frames: 48-129
- Categories: task_not_attempted
- Explanation: Following the approach, the gripper remains nearly stationary near the oven for the remaining approximately 6.7 seconds, with no visible acquisition or pulling progress (image and wrist_image, frames 48, 80, 104 and 128). The door stays closed in left_ego_image throughout this interval. This sustained unproductive pause does not advance the opening task; its underlying cause is not visible.
- Recovery: Resume task-directed alignment with the oven handle, establish a secure grasp, and pull along the door’s opening trajectory while checking clearance; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced scene objects or concrete damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so another attempt can begin without an environmental reset or human intervention.