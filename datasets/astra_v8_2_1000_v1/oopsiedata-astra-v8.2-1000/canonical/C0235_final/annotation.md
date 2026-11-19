# Episode: C0235

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the cardboard box.
- Success label: failure
- Outcome evidence: The stuffed animal remains on the table beside the box through the robot's approaches and repositioning (external and wrist, frames 0, 370, 650 and 720). The empty gripper then moves away (frames 723–744); subsequent movements and pauses do not return to the animal. The animal is still outside the box in external at frames 1106–1192, and no placement is observed through frame 1273. This is visible noncompletion with sustained unproductive behavior, not an inferred drop or confirmed failed grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 723 | No |
| 723 | 1274 | Yes |

## Failure annotations

### Failure 1

- Frames: 723-1274
- Categories: task_not_attempted
- Explanation: Starting at frame 723, the robot moves its empty gripper away from the stuffed animal, past the box toward an empty region of the table (external and wrist, frames 723–744). It subsequently makes small movements and long pauses over the empty tabletop rather than acquiring the animal (frames 823–990 and 1089–1273). The animal remains beside the box in external at frame 1192. No completed finger-closing acquisition is established, so this is annotated as sustained unproductive behavior rather than a grasp failure; its underlying cause is not visible.
- Recovery: Reacquire the animal's location, align the open fingers around its body, close and verify a secure grasp before lifting and transferring it into the box; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task is left incomplete, but no object damage, displacement or harmful collision is visible in external or wrist.
- Resetability: immediate
- Resetability evidence: The animal and box remain available on the table; another task-directed attempt requires no visible environmental resetting or human intervention.