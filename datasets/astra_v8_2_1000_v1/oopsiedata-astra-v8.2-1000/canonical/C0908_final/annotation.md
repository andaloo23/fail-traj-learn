# Episode: C0908

## Episode annotation

- Language task: Pick up the cube.
- Success label: failure
- Outcome evidence: In base_image, the gripper approaches the isolated red cube at frames 14–31, but the cube shifts sideways during the attempted acquisition at frames 32–35 and remains on the table as the empty gripper withdraws. The cube is still on the table at frame 120; this is a visibly failed acquisition, not merely unconfirmed completion. Although other cubes are visible in the right-side tray, the initial approach identifies the isolated red cube as the apparent target.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 32 | No |
| 32 | 36 | Yes |
| 36 | 121 | Yes |

## Failure annotations

### Failure 1

- Frames: 32-36
- Categories: grasp
- Explanation: In base_image frames 32–35, the gripper moves and closes while the red cube shifts to the right instead of remaining between its fingers. By frame 35 the gripper is closed and empty beside the cube, establishing failed acquisition; secure possession or a subsequent drop is not established.
- Recovery: Reopen the gripper, locate the cube at its new position, align the fingers around it, and close before attempting a controlled lift; no human intervention appears necessary.
- Severity: low
- Severity evidence: The cube is displaced on the tabletop, but no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The cube remains accessible on the table and can be approached again without an environmental reset.

### Failure 2

- Frames: 36-121
- Categories: task_not_attempted
- Explanation: After the failed acquisition, base_image frames 36–49 show the empty gripper withdrawing toward the right-side tray rather than returning to the red cube. It then remains near that area with small movements through frame 120 while the target stays stationary on the table, establishing sustained lack of task-directed progress.
- Recovery: Return attention to the visible red cube, move clear of the tray, and perform a newly aligned grasp and verified lift; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced tray contents, or harmful collision is established by the images.
- Resetability: immediate
- Resetability evidence: The target remains accessible and the scene requires no visible cleanup or physical resetting before another attempt.
