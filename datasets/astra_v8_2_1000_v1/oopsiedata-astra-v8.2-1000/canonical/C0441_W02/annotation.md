# Episode: C0441_W02

## Episode annotation

- Language task: take the small silver cup and pour its contents into the blue bowl
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this observed window: frames 350, 500, and 699 in top and right show the silver cup upright with its colored contents still inside and the blue bowl empty. Arm repositioning is visible in left and right earlier in the window, but no completed acquisition or pouring attempt is established. The latter portion shows sustained inactivity near the objects. Earlier context beyond frames 348–349 and later execution are unavailable, so this is a provisional window outcome.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 501 | No |
| 501 | 700 | Yes |

## Failure annotations

### Failure 1

- Frames: 501-700
- Categories: task_not_attempted
- Explanation: After the repositioning around frames 492–500 in right, the robot remains in substantially the same configuration through frame 699 in top, left, and right, with only small positional drift and no discernible acquisition, transport, or pouring progress for approximately 6.6 seconds. The cup and its contents remain on the table beside the empty bowl. This sustained stalling may continue beyond the supplied window; its hidden cause is not established.
- Recovery: Resume a task-directed approach, align the gripper with a secure grasp on the silver cup, verify acquisition, and then lift and tilt it over the blue bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The observed consequence is delayed task progress; no spill, damage, or hazardous contact is visible in top or right through frame 699.
- Resetability: immediate
- Resetability evidence: The cup remains upright with its contents retained and the bowl accessible, so the environment needs no visible resetting before another attempt.