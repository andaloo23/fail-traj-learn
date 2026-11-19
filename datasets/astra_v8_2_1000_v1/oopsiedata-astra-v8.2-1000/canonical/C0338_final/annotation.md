# Episode: C0338

## Episode annotation

- Language task: put the corn on the green cloth
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot approaches the corn in frames 0–12, but the corn shifts outside the left finger rather than being acquired in frames 13–20. At frame 20 it remains on the bare table and the green cloth remains empty. The visible acquisition attempt is unsuccessful; no completed transfer is shown.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 13 | No |
| 13 | 21 | Yes |

## Failure annotations

### Failure 1

- Frames: 13-21
- Categories: grasp
- Explanation: In right_shoulder_cam frame 13, the corn is displaced sideways outside the left gripper finger. Through frames 14–20, the fingers draw closer and the gripper shifts back without securing the corn between them; the corn remains on the table instead of being lifted for transfer.
- Recovery: Reopen the gripper, reposition above the corn's updated location with the fingers on opposite sides, and acquire and verify a secure grasp before lifting toward the cloth. No human intervention appears necessary.
- Severity: low
- Severity evidence: The corn is shifted on the tabletop, but no damage or meaningful damage risk is visible in right_shoulder_cam frames 13–20.
- Resetability: immediate
- Resetability evidence: The corn remains accessible on the table and the cloth is undisturbed; another aligned grasp can be attempted without an environmental reset.