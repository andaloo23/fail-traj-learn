# Episode: C0120

## Episode annotation

- Language task: Pick up the ball and place it in the bowl.
- Success label: failure
- Outcome evidence: The orange ball starts beside the blue bowl (frame 0, camera_high). Repeated acquisition attempts are followed by empty withdrawal while the ball remains on the table (frames 197, 387 and 651, camera_high and camera_wrist_right). At frame 749, camera_high and camera_wrist_right show the gripper near the ball, still outside the bowl; completion is not visible. The earlier acquisitions visibly fail, whereas the final attempt has no confirmed outcome.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 174 | No |
| 174 | 206 | Yes |
| 206 | 358 | No |
| 358 | 504 | Yes |
| 504 | 629 | No |
| 629 | 656 | Yes |
| 656 | 750 | No |

## Failure annotations

### Failure 1

- Frames: 174-206
- Categories: grasp
- Explanation: After closing near the ball, the gripper withdraws without it beginning at frame 174; by frames 193-205, camera_high and camera_wrist_right show the ball remaining on the table and the empty gripper moving toward the bowl. This acquisition did not advance the required transfer; the precise contact failure is obscured.
- Recovery: Return with the fingers open, align them on opposite sides of the ball, close and verify retention with a small lift before transferring; no human intervention is needed.
- Severity: low
- Severity evidence: The ball remains on the tabletop, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The ball and bowl remain accessible and usable; another grasp can be attempted without environmental intervention.

### Failure 2

- Frames: 358-504
- Categories: grasp
- Explanation: The next acquisition is again followed by empty withdrawal, starting at frame 358. Frames 375-397 in camera_high and camera_wrist_right establish that the ball remains outside the bowl while the gripper moves away; it subsequently opens near the empty bowl and retracts through frame 503 without transferring the ball.
- Recovery: Reacquire the ball rather than continuing an empty placement motion; adjust grasp alignment and verify that the ball moves with the gripper before transport. No human intervention is needed.
- Severity: low
- Severity evidence: The unsuccessful acquisition leaves the ball on the table; no damage is visible.
- Resetability: immediate
- Resetability evidence: No cleanup or object restoration is required, and both task objects remain within the workspace.

### Failure 3

- Frames: 629-656
- Categories: grasp
- Explanation: Following another closing attempt, the gripper moves away empty beginning at frame 629. Frames 643-653 in camera_high show the ball remaining on the tabletop beneath and separate from the withdrawing gripper, while camera_wrist_right shows empty fingers. A renewed approach begins at frame 656.
- Recovery: Reopen and recenter the fingers around the ball, obtain a secure grasp and confirm a small lift before moving toward the bowl; no human intervention is needed.
- Severity: low
- Severity evidence: Only acquisition is prevented; no visible damage or consequential scene disturbance occurs.
- Resetability: immediate
- Resetability evidence: The ball remains available on the tabletop and the bowl remains upright, permitting an immediate retry without a human reset.