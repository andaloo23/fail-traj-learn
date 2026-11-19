# Episode: C0873

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot approaches the drawer cabinet and repeatedly attempts to acquire a silver handle, but no drawer opens. In wrist_image, frames 92–113 show closure followed by withdrawal without the handle; further attempts occur around frames 141–169, 186–210, and 235–262. The cabinet remains closed in left_ego_image through frame 399. This is visibly unsuccessful acquisition, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 101 | No |
| 101 | 120 | Yes |
| 120 | 149 | No |
| 149 | 170 | Yes |
| 170 | 196 | No |
| 196 | 211 | Yes |
| 211 | 247 | No |
| 247 | 263 | Yes |
| 263 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 101-120
- Categories: grasp
- Explanation: Following closure near the handle, the gripper withdraws without pulling it in wrist_image, frames 101–113, then opens at frames 114–120; left_ego_image shows the drawer remaining closed.
- Recovery: Reposition the open fingers around the projecting handle, verify acquisition, and pull along the drawer travel direction; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt fails without visible damage or disturbance of other objects.
- Resetability: immediate
- Resetability evidence: The handle and cabinet remain in place, allowing another attempt without environmental resetting.

### Failure 2

- Frames: 149-170
- Categories: grasp
- Explanation: In wrist_image, frames 149–154 show another withdrawal leaving the handle behind; subsequent finger opening and closing through frame 169 does not establish acquisition or move the drawer, also unchanged in left_ego_image.
- Recovery: Adjust finger placement and approach depth rather than repeat closure at the same ineffective position; no human intervention is visibly required.
- Severity: low
- Severity evidence: No damage is visible; the consequence is another unsuccessful handle acquisition.
- Resetability: immediate
- Resetability evidence: No displaced objects or damaged components need resetting.

### Failure 3

- Frames: 196-211
- Categories: grasp
- Explanation: After another closure, wrist_image frames 196–203 show the gripper retreating while the silver handle stays on the closed drawer; the fingers reopen at frames 204–211. left_ego_image confirms no drawer extension.
- Recovery: Reacquire the handle with fingers securely on opposing sides before attempting a controlled outward pull; no human assistance is visibly necessary.
- Severity: low
- Severity evidence: Only task progress is lost; no meaningful damage or damage risk is established.
- Resetability: immediate
- Resetability evidence: The scene remains usable and unchanged for a new attempt.

### Failure 4

- Frames: 247-263
- Categories: grasp
- Explanation: wrist_image frames 247–255 again show withdrawal with closed fingers but no retained handle, followed by reopening through frame 262; left_ego_image shows the drawer still closed.
- Recovery: Change the grasp alignment and verify handle capture before withdrawing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The missed acquisition produces no visible damage or unrelated object movement.
- Resetability: immediate
- Resetability evidence: Another attempt can begin without restoring the environment.

### Failure 5

- Frames: 263-400
- Categories: task_not_attempted
- Explanation: After reopening, the robot remains near the cabinet with only small finger and pose adjustments, without renewed effective acquisition or drawer motion. wrist_image and left_ego_image at frames 263, 300, 340, and 399 establish sustained unproductive hovering rather than a brief pause.
- Recovery: Resume a deliberately realigned handle acquisition and controlled pull; if acquisition cannot be verified, stop and request assistance rather than continue ineffective repetitions.
- Severity: low
- Severity evidence: The drawer remains closed, with no visible damage or harmful side effects.
- Resetability: immediate
- Resetability evidence: The stalled behavior leaves no environmental change requiring a reset.