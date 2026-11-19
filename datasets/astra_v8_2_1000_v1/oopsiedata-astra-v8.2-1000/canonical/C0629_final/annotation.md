# Episode: C0629

## Episode annotation

- Language task: Open the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven starts closed in frame 0 (image, left_ego_image). The first pull partially opens the door around frames 81–94, but the gripper moves away and the door returns closed by frame 104 (image, left_ego_image). After repositioning and retrying, the robot opens the door downward in frames 191–208; it remains open with the interior exposed through frame 225 (image, left_ego_image). No damage or displacement of unrelated objects is visibly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 95 | No |
| 95 | 112 | Yes |
| 112 | 226 | No |

## Failure annotations

### Failure 1

- Frames: 95-112
- Categories: grasp
- Explanation: Following the partial opening visible in frames 81–94, the gripper separates from the handle and continues away without retaining it in frames 95–111; the door swings back closed by frame 104 (image, left_ego_image). The empty fingers are also visible in wrist_image. This loses the opening progress rather than completing the pull.
- Recovery: Reposition at the handle, establish a secure grasp, and maintain engagement while following the door’s downward opening arc until it stays open; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The door returns closed and the attempt must be repeated; no damage or meaningful damage risk is visibly established.
- Resetability: immediate
- Resetability evidence: The oven remains upright, closed, and accessible, with no displaced objects requiring intervention before another attempt.