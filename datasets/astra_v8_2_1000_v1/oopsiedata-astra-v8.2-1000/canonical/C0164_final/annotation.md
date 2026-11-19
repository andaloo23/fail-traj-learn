# Episode: C0164

## Episode annotation

- Language task: Pick up the ball and place it in the bowl.
- Success label: failure
- Outcome evidence: The right gripper approaches and briefly lifts the orange ball (frames 140–155, camera_wrist_right and camera_wrist_left), but the ball separates and returns to the table (frames 157–165, camera_high and camera_wrist_left). Subsequent empty-gripper movement does not place it in the blue bowl. At frame 749, camera_high and camera_wrist_right show the ball still outside the bowl; this is a visibly unsuccessful attempt, not merely an occluded or unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 157 | No |
| 157 | 305 | Yes |
| 305 | 560 | No |
| 560 | 750 | Yes |

## Failure annotations

### Failure 1

- Frames: 157-305
- Categories: grasp
- Explanation: The ball separates from the right gripper during lifting at frames 157–159 and is visibly left on the table by frames 162–165 (camera_high and camera_wrist_left). The empty gripper continues toward and over the bowl through frames 175–275 before withdrawing, without transferring the ball (camera_high and camera_wrist_right). The visible failure is loss of retention; its underlying cause is not established.
- Recovery: Locate the ball again, align open fingers around it, acquire it securely, and verify retention with a short lift before transporting it over the bowl; human intervention is not needed for the visible state.
- Severity: low
- Severity evidence: The ball returns to the tabletop and remains accessible; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: Both objects remain upright or usable on the table, so another grasp can be attempted without environmental intervention.

### Failure 2

- Frames: 560-750
- Categories: task_not_attempted
- Explanation: After repositioning, the robot remains near the ball and bowl with only small gripper or pose changes, without acquiring the ball or making sustained progress for the rest of the episode (frames 560, 600, 650, 700 and 749, camera_high and camera_wrist_right). This sustained unproductive interval is distinct from the earlier retention failure; no abnormal shutdown is visible.
- Recovery: Resume a task-directed approach to the ball, center the fingers on opposite sides, and verify a secure grasp before lifting and placing it in the bowl; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but the stationary ball, bowl and surrounding scene show no damage or supported material hazard.
- Resetability: immediate
- Resetability evidence: The ball remains accessible beside the bowl and no cleanup or object reset is necessary before resuming.
