# Episode: C0997

## Episode annotation

- Language task: put the corn on the green cloth
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot approaches the corn in frames 5–15 but displaces it outside the gripper in frames 16–18. The gripper subsequently moves away empty, while the corn remains on the bare table and the green cloth remains empty through frame 40. This is a visibly unsuccessful acquisition, not merely unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 16 | No |
| 16 | 41 | Yes |

## Failure annotations

### Failure 1

- Frames: 16-41
- Categories: grasp
- Explanation: In right_shoulder_cam frames 16–18, the corn rotates and shifts away from the fingers rather than becoming enclosed. In frames 19–38, the gripper continues moving beside the corn without acquiring it; by frames 39–40 it moves away empty, leaving the corn on the table instead of transferring it to the cloth.
- Recovery: Raise and reopen the gripper, realign around the corn’s updated position, then acquire it and verify retention before lifting and placing it on the green cloth. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The corn is displaced on the tabletop, but no damage, spill, or meaningful damage risk is visible in right_shoulder_cam through frame 40.
- Resetability: immediate
- Resetability evidence: The corn remains accessible on the table and the cloth remains clear; another attempt requires updated alignment but no environmental reset or human intervention.