# Episode: C0085

## Episode annotation

- Language task: Pick up the green cup and stack it on the purple cup.
- Success label: failure
- Outcome evidence: The cups start separately on the table in camera_high at frame 0. The robot approaches the green cup, but subsequently moves away empty while the cup remains on the table (frames 332–400, camera_wrist_left and camera_high). Both cups remain separate at frames 480 and 599 in camera_high; camera_wrist_right also shows them separate at frame 599. A renewed approach is visible near the end, but its acquisition and stacking are unconfirmed; the earlier empty withdrawal establishes a visibly failed attempt.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 332 | No |
| 332 | 504 | Yes |
| 504 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 332-504
- Categories: grasp
- Explanation: After closing near the green cup, the gripper begins withdrawing without it around frame 332. In camera_wrist_left at frames 342–400, the empty fingers move away while the green cup stays on the table; camera_high confirms that the cups remain separate. The ensuing empty movement through frames 406–503 does not transport the green cup or advance stacking. The images do not establish the underlying cause of the failed acquisition.
- Recovery: Reopen the gripper, realign around the green cup, acquire it securely, and verify that it lifts with the gripper before transporting it above the purple cup; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The green cup remains on the tabletop, with no visible damage, spill, or meaningful damage risk in camera_high and camera_wrist_left at frames 350–503.
- Resetability: immediate
- Resetability evidence: Both cups remain accessible and separate on the table, so another grasp can be attempted without an environmental reset or human intervention.