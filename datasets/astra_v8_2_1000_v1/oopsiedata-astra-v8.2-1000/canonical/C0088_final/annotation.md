# Episode: C0088

## Episode annotation

- Language task: Pick up the apple from the bowl and put it on the table.
- Success label: failure
- Outcome evidence: The apple remains in the bowl throughout the episode. Frames 153–163 and 207–228 in wrist_cam show closed fingers withdrawing without the apple; left_base_cam and right_base_cam corroborate that it stays in the bowl. At frame 240, all three cameras still show the apple in the bowl rather than on the table. This is a visibly unsuccessful acquisition, not merely unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 153 | No |
| 153 | 164 | Yes |
| 164 | 207 | No |
| 207 | 212 | Yes |
| 212 | 225 | No |
| 225 | 229 | Yes |
| 229 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 153-164
- Categories: grasp
- Explanation: At frame 153 in wrist_cam, the fingers have closed without securing the apple; through frame 163 they withdraw while the apple remains in the bowl. left_base_cam and right_base_cam confirm no successful lift. Reopening begins at frame 164.
- Recovery: Open the fingers, realign them around opposite sides of the apple with clearance from the bowl, and verify acquisition with a small lift before transporting it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The apple remains contained in the bowl, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The apple is still accessible in the bowl, so another attempt requires no environmental reset or human intervention.

### Failure 2

- Frames: 207-212
- Categories: grasp
- Explanation: Frames 207–211 in wrist_cam show another closure followed by empty withdrawal while the apple stays behind; left_base_cam and right_base_cam likewise show it remaining in the bowl. The fingers begin reopening at frame 212.
- Recovery: Reopen and adjust the grasp position and depth so that the fingers surround the apple rather than closing short of it, then verify retention before lifting farther; no human intervention is visibly needed.
- Severity: low
- Severity evidence: This attempt fails to acquire the apple without visible damage or displacement outside the bowl.
- Resetability: immediate
- Resetability evidence: The scene remains usable for a direct retry, with no cleanup or object replacement needed.

### Failure 3

- Frames: 225-229
- Categories: grasp
- Explanation: Following reopening and adjustment, wrist_cam shows the fingers closing empty again at frame 225 and remaining empty through frame 228 as the arm retreats. The apple remains in the bowl in left_base_cam and right_base_cam. Reopening starts at frame 229.
- Recovery: Reassess the apple’s position relative to the fingertips, approach with the fingers open, and establish a verified grasp before withdrawing; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only task completion is prevented; no damage, spill, or harmful side effect is visible.
- Resetability: immediate
- Resetability evidence: The apple and bowl remain available in the workspace, allowing another attempt without environmental intervention.