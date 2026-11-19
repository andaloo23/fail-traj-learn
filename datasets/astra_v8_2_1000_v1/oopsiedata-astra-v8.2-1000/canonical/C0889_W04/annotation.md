# Episode: C0889_W04

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: This is a provisional window outcome: no additional toy placement is visible, and toys remain on the table in overhead_cam at frame 1399. wrist_cam at frames 1136–1147 shows the fingers closing beside the pink toy; frames 1205–1234 show the closed, empty gripper moving separately from that toy. A beige toy is visible at the plate edge in wrist_cam at frames 1355–1363, but its placement occurred outside this window. No unwanted collision is clearly established. Earlier context beyond frames 1048–1049 and later execution are unavailable; the window end does not establish episode termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1136 | Yes |
| 1136 | 1144 | No |
| 1144 | 1220 | Yes |
| 1220 | 1234 | No |
| 1234 | 1400 | Yes |

## Failure annotations

### Failure 1

- Frames: 1050-1136
- Categories: task_not_attempted
- Explanation: overhead_cam and wrist_cam at frames 1050, 1080, 1110 and 1135 show the open gripper remaining beside the pink toy with only small adjustments and no acquisition or transfer for roughly six seconds. This independently supports sustained stalling, consistent with the supplied context frames 1048–1049; its earlier onset cannot be verified here. Finger closure begins at frame 1136.
- Recovery: Align the fingers around an accessible toy and perform a verified grasp and lift while maintaining clearance; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is delay, with no observed damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toys and plate remain accessible, and no environmental intervention is required to resume.

### Failure 2

- Frames: 1144-1220
- Categories: grasp
- Explanation: wrist_cam at frames 1144–1147 shows the fingers completing closure beside rather than around the pink toy. The robot then moves toward and alongside the plate with the fingers closed and empty, while the pink toy remains on the tabletop, as confirmed across overhead_cam and wrist_cam at frames 1160, 1205 and 1213. This is a failed acquisition rather than merely an unfinished closing action. The interval ends when movement back toward the toys begins around frame 1220.
- Recovery: Return with adequate clearance, open the gripper, center a toy between the fingers, and verify possession with a short lift before attempting transfer; human intervention is not visibly required.
- Severity: low
- Severity evidence: The attempted acquisition fails without visible damage, dropping or a clearly established collision.
- Resetability: immediate
- Resetability evidence: The missed toy remains on the accessible tabletop; another attempt requires no environmental reset.

### Failure 3

- Frames: 1234-1400
- Categories: task_not_attempted
- Explanation: After returning toward the toys, the robot repeatedly shifts its closed, empty gripper near the plate without acquiring or transferring a toy. overhead_cam and wrist_cam at frames 1234, 1275, 1300, 1330, 1360 and 1397 show these back-and-forth adjustments while the toys remain on the table. The sustained motion does not visibly advance the task. The fingers begin opening at frames 1398–1399, but a renewed aligned attempt is not yet established; this unproductive interval may continue beyond the window.
- Recovery: Stop the repeated empty movements, locate an accessible toy, open and align the fingers around it, and verify acquisition before moving to the plate; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: Only lost progress and delay are established; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The scene remains usable and the toys remain accessible, so no human reset is visibly needed.