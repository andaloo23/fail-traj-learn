# Episode: C0936

## Episode annotation

- Language task: Pick up the spoon and place it into the box.
- Success label: failure
- Outcome evidence: Four acquisitions fail as the gripper rises empty while the spoon remains on the table (wrist_right, frames 58–62, 94–99, 139–144, and 206–213). The other gripper subsequently lifts the spoon (wrist_left and ceiling, frames 275–286), but it falls back onto the tabletop beside the box during transport (frames 287–291). At frame 300, ceiling and wrist_left show the spoon outside the box; this is a visibly failed attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 53 | No |
| 53 | 63 | Yes |
| 63 | 90 | No |
| 90 | 100 | Yes |
| 100 | 135 | No |
| 135 | 145 | Yes |
| 145 | 202 | No |
| 202 | 214 | Yes |
| 214 | 287 | No |
| 287 | 301 | Yes |

## Failure annotations

### Failure 1

- Frames: 53-63
- Categories: grasp
- Explanation: The fingers finish closing without securing the spoon (wrist_left, frame 53); the gripper then rises empty while the spoon stays on the tabletop (wrist_right, frames 56–62), preventing pickup.
- Recovery: Reopen, realign the fingers around a graspable part of the spoon at the correct height, and verify retention with a small lift; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon remains on the table, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible for another attempt without environmental intervention.

### Failure 2

- Frames: 90-100
- Categories: grasp
- Explanation: The second closure again fails to secure the spoon (wrist_left, frame 90), followed by an empty lift with the spoon still on the table (wrist_right and ceiling, frames 93–99).
- Recovery: Adjust the grasp position and height rather than repeat the same closure, then confirm pickup before transport; no human intervention is needed.
- Severity: low
- Severity evidence: Only acquisition fails; no damage is visible.
- Resetability: immediate
- Resetability evidence: The spoon and box remain available in the workspace without a required reset.

### Failure 3

- Frames: 135-145
- Categories: grasp
- Explanation: The gripper closes again without retaining the spoon (wrist_left, frame 135) and withdraws upward empty (wrist_right, frames 137–144), leaving the target on the tabletop.
- Recovery: Reassess the spoon's position and choose a different grasp alignment or the other gripper, verifying retention before moving toward the box; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition causes no visible damage or hazardous displacement.
- Resetability: immediate
- Resetability evidence: Another grasp can be attempted directly with the spoon still accessible.

### Failure 4

- Frames: 202-214
- Categories: grasp
- Explanation: A fourth closure fails to capture the spoon (wrist_left, frame 202); the gripper lifts away while the spoon remains stationary on the table (wrist_right, frames 205–213).
- Recovery: Use a revised grasp location or the other gripper and perform a short retention check before transport; no human intervention is needed.
- Severity: low
- Severity evidence: The consequence is another unsuccessful pickup, with no visible damage.
- Resetability: immediate
- Resetability evidence: No cleanup or object replacement is necessary for a new attempt.

### Failure 5

- Frames: 287-301
- Categories: grasp
- Explanation: After the other gripper visibly lifts and carries the spoon (wrist_left, frames 275–286), the spoon slips downward and lands on the table outside the box (wrist_left and ceiling, frames 287–291). The gripper continues toward the box without completing placement, and the spoon remains outside through frame 300.
- Recovery: Return to the spoon's observed tabletop position, establish and verify a secure grasp, then carry it over the box and release inside; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon falls onto the tabletop and remains intact; no damage to the box, robot, or surrounding scene is visible.
- Resetability: immediate
- Resetability evidence: The dropped spoon remains accessible beside the box and can be reacquired without environmental resetting.