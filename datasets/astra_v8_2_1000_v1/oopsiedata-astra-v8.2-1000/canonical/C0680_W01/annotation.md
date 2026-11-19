# Episode: C0680_W01

## Episode annotation

- Language task: flip the small box upside down
- Success label: failure
- Outcome evidence: No box is visibly flipped in this window: frames 0 and 349 in top show the objects in essentially unchanged positions and orientations, while left and right show no completed inversion. The robot initially remains stationary, then repositions its left gripper near the pink rectangular object (frames 222–349, left and top). The task does not uniquely identify which visible box is intended. Completion is unconfirmed rather than a visibly failed flipping attempt; later episode context is absent, so this outcome is provisional.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 222 | Yes |
| 222 | 350 | No |

## Failure annotations

### Failure 1

- Frames: 0-222
- Categories: task_not_attempted
- Explanation: Across frames 0–221 in left, right and top, both grippers remain essentially stationary and all objects retain their positions and orientations for approximately 7.4 seconds, with no discernible approach or flipping attempt. This sustained inactivity does not advance the task; no hidden cause is established. Visible repositioning begins at frame 222.
- Recovery: Identify the intended small box, requesting clarification if needed, then approach it with a clear path and establish a controlled grasp before inverting it; no physical human intervention is visibly needed.
- Severity: low
- Severity evidence: The observed consequence is delay only; no object displacement, damage or meaningful damage risk is visible during the stationary interval.
- Resetability: immediate
- Resetability evidence: The scene remains unchanged and available for an attempt, so no environmental reset or physical intervention is needed.