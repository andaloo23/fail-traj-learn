# Episode: C0214

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door starts open at frame 0, rises partway toward closed in frames 38–48, and returns to its lowered, open position by frame 89 (image, left_ego_image). Subsequent adjustments do not close it; it remains visibly open at frame 296 (image, left_ego_image). This is a visibly unsuccessful closing attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 55 | No |
| 55 | 118 | Yes |
| 118 | 143 | No |
| 143 | 297 | Yes |

## Failure annotations

### Failure 1

- Frames: 55-118
- Categories: manipulation
- Explanation: After raising the door partway in frames 38–48, the robot moves it back downward beginning around frame 55; it is open again by frame 89. Small subsequent movements around frames 106–117 do not restore the closing progress (image, left_ego_image). Door control was demonstrated by the earlier coordinated lift, but the closing manipulation failed; the images do not establish a hidden mechanical cause.
- Recovery: Reposition securely at the handle and guide the door upward along its hinge arc until it seats closed, checking that the gripper clears the closing gap; no human intervention is visibly required.
- Severity: low
- Severity evidence: The door returns to its open position without visible breakage, displaced surrounding objects, or other damage (image, left_ego_image, frame 118).
- Resetability: immediate
- Resetability evidence: The oven remains upright and its handle accessible; another closing attempt requires no visible environmental reset.

### Failure 2

- Frames: 143-297
- Categories: task_not_attempted
- Explanation: Following wrist and gripper repositioning in frames 118–142, the robot remains near the open door with only small movements and no meaningful closing progress for the rest of the episode (image, left_ego_image, wrist_image; frames 143, 180, 240, and 296). This extended unproductive interval is sustained stalling, rather than a brief alignment pause.
- Recovery: Resume a deliberate handle alignment and controlled upward closing motion, then verify that the door remains seated; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The visible consequence is an unfinished task and prolonged delay; no damage or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The open door and surrounding scene remain available for a new attempt without cleanup, repair, or object replacement.