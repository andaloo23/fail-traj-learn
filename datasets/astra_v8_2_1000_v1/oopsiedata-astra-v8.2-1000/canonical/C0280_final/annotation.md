# Episode: C0280

## Episode annotation

- Language task: Pick up the red block and put it on the yellow rectangle.
- Success label: failure
- Outcome evidence: The robot approaches the objects but never visibly lifts or places the red block. In right_base_cam and wrist_cam, the red block remains beside the yellow rectangle at frames 0, 134, and 240. The episode includes prolonged near-target hovering and a withdrawal followed by another approach; completion is not confirmed, and no completed grasp or drop is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 34 | No |
| 34 | 102 | Yes |
| 102 | 193 | No |
| 193 | 241 | Yes |

## Failure annotations

### Failure 1

- Frames: 34-102
- Categories: task_not_attempted
- Explanation: Following the approach, the robot remains near the red block with only small positional changes and no visible acquisition or task progress for approximately seven seconds. Frames 34, 60, 80, and 101 in wrist_cam show the block outside the open gripper, while right_base_cam shows no lift or transfer. More substantial repositioning resumes at frame 102.
- Recovery: Reassess the red block's position, align the open fingers on opposite sides, and execute a controlled grasp followed by a small verification lift; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The observed consequence is lost progress; no damage, dropped object, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: Both task objects remain accessible on the tabletop, so another attempt requires no environmental reset.

### Failure 2

- Frames: 193-241
- Categories: task_not_attempted
- Explanation: After withdrawing and approaching again, the robot spends the remaining interval hovering near the red block with small back-and-forth adjustments but no visible acquisition. Frames 193, 210, 225, and 240 in wrist_cam and right_base_cam show the red block still on the table beside the yellow rectangle. This is sustained unproductive behavior rather than evidence of a completed failed grasp.
- Recovery: Re-localize the block and correct the grasp alignment instead of continuing near-stationary adjustments, then verify possession before transporting it to the yellow rectangle; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but the images show no damage or harmful disturbance of the scene.
- Resetability: immediate
- Resetability evidence: The block and destination remain available for an immediate retry without cleanup or manual repositioning.