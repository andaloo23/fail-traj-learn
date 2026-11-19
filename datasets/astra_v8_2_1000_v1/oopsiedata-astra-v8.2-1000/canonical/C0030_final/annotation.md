# Episode: C0030

## Episode annotation

- Language task: Pick up the ball and place it in the bowl.
- Success label: failure
- Outcome evidence: The orange ball remains on the tabletop outside the blue bowl, including at frames 250, 500 and 749 in camera_high. camera_wrist_right shows the gripper moving away without the ball on multiple attempts and the ball still outside the bowl at frame 749. This is visibly unsuccessful acquisition, not merely an unconfirmed final placement; no completed transfer into the bowl is observed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 201 | No |
| 201 | 297 | Yes |
| 297 | 478 | No |
| 478 | 505 | Yes |
| 505 | 643 | No |
| 643 | 657 | Yes |
| 657 | 750 | No |

## Failure annotations

### Failure 1

- Frames: 201-297
- Categories: grasp
- Explanation: After positioning and closing near the ball, the gripper starts withdrawing empty at frame 201 and moves toward the bowl without acquiring the ball. camera_high shows the ball left on the table at frames 219–250, while camera_wrist_right shows the empty fingers over the bowl at frames 251–294. This motion does not transfer the target.
- Recovery: Return to the ball, center the open fingers around its sides, close and verify retention with a small lift before moving toward the bowl; no human intervention is needed.
- Severity: low
- Severity evidence: The ball and bowl remain on the tabletop with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The ball remains accessible in its original working area; another acquisition attempt requires no environmental reset.

### Failure 2

- Frames: 478-505
- Categories: grasp
- Explanation: Following another approach and finger closure near the ball, the gripper withdraws empty beginning at frame 478. camera_high shows increasing separation while the ball stays on the table through frame 504; camera_wrist_right shows the ball outside the fingers at frames 494–504.
- Recovery: Reapproach with corrected finger alignment and grasp height, then confirm that the ball rises with the gripper before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: This missed acquisition prevents progress but produces no visible damage or harmful displacement.
- Resetability: immediate
- Resetability evidence: Both task objects remain accessible and usable without manual resetting.

### Failure 3

- Frames: 643-657
- Categories: grasp
- Explanation: The next acquisition again ends with the gripper lifting away empty. At frames 643–651, camera_high shows the fingers separating from the ball while it remains on the tabletop; camera_wrist_right shows the ball passing below the empty fingers rather than being carried. The subsequent return toward the ball begins at frame 657.
- Recovery: Recenter the fingers around the ball and check acquisition with a short vertical lift; continue to the bowl only after visible retention is established. Human intervention is not needed.
- Severity: low
- Severity evidence: The ball remains on the work surface, and no damage or other harmful side effect is visible.
- Resetability: immediate
- Resetability evidence: The missed grasp leaves the scene ready for another attempt, with no cleanup or object replacement required.