# Episode: C0144

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot makes three spoon acquisition attempts but never transfers the spoon to the drawer. In left_ego_image and wrist_image, the spoon falls back onto the table at frames 91–95, remains behind after the second attempt at frames 171–174, and falls again at frames 251–259. At frame 399, image and left_ego_image still show the spoon on the tabletop outside the drawer; this is a visibly unsuccessful episode, not merely unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 89 | No |
| 89 | 108 | Yes |
| 108 | 167 | No |
| 167 | 200 | Yes |
| 200 | 249 | No |
| 249 | 263 | Yes |
| 263 | 314 | No |
| 314 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 89-108
- Categories: grasp
- Explanation: After lifting the spoon, the handle slides out of the fingers at frames 89–91 in wrist_image. The spoon falls onto the table at frames 92–95 in left_ego_image, while the gripper continues upward empty rather than transporting it.
- Recovery: Re-localize the spoon, align the fingers around a secure portion of its handle, and verify retention with a small lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon lands on the tabletop without visible damage or disruption to other objects.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the table, so another grasp can be attempted without environmental intervention.

### Failure 2

- Frames: 167-200
- Categories: grasp
- Explanation: The second acquisition does not retain the spoon: at frames 167–171 in wrist_image the fingers rise away from the handle, and frames 171–174 in left_ego_image show the spoon remaining on the tabletop. The arm subsequently retreats empty.
- Recovery: Open the gripper, correct its alignment and contact depth around the handle, and verify that the spoon follows a short test lift; no human intervention is needed.
- Severity: low
- Severity evidence: This attempt leaves the spoon on the table with no visible damage or meaningful collateral disturbance.
- Resetability: immediate
- Resetability evidence: The target remains reachable and the scene needs no manual reset.

### Failure 3

- Frames: 249-263
- Categories: grasp
- Explanation: The third attempt initially lifts the spoon, but its handle slips downward at frames 249–251 in wrist_image. In left_ego_image, frames 251–259 show it falling and settling back onto the tabletop while the gripper withdraws empty.
- Recovery: Re-localize the displaced spoon and use a more secure handle grasp, confirming retention before moving toward the drawer; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon falls only onto the table; no breakage or damage to surrounding objects is visible.
- Resetability: immediate
- Resetability evidence: Although displaced, the spoon remains on the accessible tabletop and requires no external reset.

### Failure 4

- Frames: 314-400
- Categories: task_not_attempted
- Explanation: After moving toward the drawer empty, the robot remains essentially stationary beside it from frame 314 through frame 399 in image and wrist_image. Throughout this sustained interval, left_ego_image shows the spoon still on the table, with no renewed acquisition or placement progress.
- Recovery: Resume task-directed action by locating and securely acquiring the spoon, then placing it inside the open drawer; no human intervention is visibly required.
- Severity: low
- Severity evidence: The sustained inactivity prevents completion but causes no visible damage or additional hazard.
- Resetability: immediate
- Resetability evidence: The scene remains usable, with the spoon on the table and the drawer available; no environmental reset is necessary.