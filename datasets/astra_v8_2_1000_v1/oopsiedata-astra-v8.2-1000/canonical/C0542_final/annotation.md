# Episode: C0542

## Episode annotation

- Language task: pick up the cube
- Success label: success but suboptimal
- Outcome evidence: The first acquisition misses: frames 18–24 show finger closure beside the cube in wrist_image_left, and frames 26–32 show the gripper withdrawing empty while the cube remains on the mat in exterior_image_1_left. The robot then realigns and grasps the cube; frames 50–53 in exterior_image_1_left show it lifted clear of the mat, while wrist_image_left shows it retained between the fingers.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 18 | No |
| 18 | 33 | Yes |
| 33 | 54 | No |

## Failure annotations

### Failure 1

- Frames: 18-33
- Categories: grasp
- Explanation: In frames 18–24, wrist_image_left shows the fingers closing without capturing the offset cube. The gripper subsequently withdraws empty in frames 26–32, while exterior_image_1_left shows the cube remaining on the mat, establishing a failed acquisition rather than merely an unfinished closure. Task-directed realignment begins at frame 33.
- Recovery: Reopen the gripper, align the fingers on opposite sides of the cube, descend to a suitable grasp height, and close before lifting and checking retention; no human intervention is needed.
- Severity: low
- Severity evidence: The missed grasp leaves the cube on the mat, with no visible damage or harmful disturbance in exterior_image_1_left.
- Resetability: immediate
- Resetability evidence: The cube remains accessible on the mat and the scene needs no resetting or human intervention before another attempt.