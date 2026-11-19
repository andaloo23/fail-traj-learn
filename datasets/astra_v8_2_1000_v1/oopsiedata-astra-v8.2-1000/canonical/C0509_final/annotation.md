# Episode: C0509

## Episode annotation

- Language task: Pick up the green cup and stack it on the purple cup.
- Success label: failure
- Outcome evidence: camera_high shows the initially separate cups at frame 0 and still separate at frame 599. During the first acquisition, the green cup tips onto its side rather than being retained (camera_wrist_right, frames 130–158), and the gripper moves away empty. A later closing-and-withdrawing motion also leaves the cup behind (frames 285–320, camera_high and camera_wrist_left). No stack is formed; the final renewed approach does not visibly establish acquisition or completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 130 | No |
| 130 | 205 | Yes |
| 205 | 304 | No |
| 304 | 410 | Yes |
| 410 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 130-205
- Categories: grasp
- Explanation: The green cup tips during acquisition at frames 130–140 in camera_wrist_right and is left lying on the table as the empty gripper moves toward the purple cup at frames 158–190. camera_high confirms that the green cup remains behind and moves farther from its original position rather than being carried into a stack.
- Recovery: Locate the displaced green cup, acquire it securely from its sideways pose, and restore an upright orientation before moving above the purple cup; human intervention is not necessarily needed.
- Severity: low
- Severity evidence: The cup topples on the work surface, with no visible breakage, spill, or damage in camera_high and camera_wrist_right.
- Resetability: minor_reset
- Resetability evidence: Restoring the cup upright is a straightforward small reset; it remains on the accessible work surface and does not require repair or difficult retrieval.

### Failure 2

- Frames: 304-410
- Categories: grasp
- Explanation: Following finger closure around frames 285–294, the gripper withdraws empty beginning at frame 304 while the green cup remains on the table (camera_high and camera_wrist_left, frames 304–320). It then stays near the purple cup with small adjustments through frame 409 without carrying the green cup or advancing the stack.
- Recovery: Return to the green cup's actual position, align the fingers around its body, and verify retention with a small lift before transporting it; no human intervention is required for this missed acquisition.
- Severity: low
- Severity evidence: This attempt leaves the cups separate without visible additional damage or a supported meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The missed acquisition causes no new environmental condition requiring resetting; the robot can immediately reattempt acquisition from the cup's existing pose.