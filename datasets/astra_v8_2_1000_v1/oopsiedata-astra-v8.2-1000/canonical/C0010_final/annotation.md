# Episode: C0010

## Episode annotation

- Language task: put the corn on the green cloth
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot grasps and lifts the corn in frames 20–32 and carries it above the green cloth in frames 38–44. It then moves the corn to the right and lowers it beside the cloth in frames 47–57. Frames 58–69 show the corn still at the gripper, outside the cloth; successful placement and release are not visible. The off-target movement is observed, while final release remains unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 47 | No |
| 47 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 47-70
- Categories: manipulation
- Explanation: After establishing control of the corn and bringing it above the cloth, the robot moves it farther right beginning at frame 47 in right_shoulder_cam, then lowers it beside rather than onto the cloth in frames 50–57. It remains there through frame 69 without a visible successful placement. This off-target transport and lowering fails to accomplish the intended placement; no slipping or release is established.
- Recovery: While maintaining a secure grasp, lift the corn clear of the table, realign it over the cloth, lower it onto the cloth, and release once supported. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The corn remains at the gripper beside the cloth, with no visible damage, spill, or harmful contact with unrelated objects in right_shoulder_cam frames 57–69.
- Resetability: immediate
- Resetability evidence: The cloth and corn remain accessible and the scene is intact; the robot can reposition the held corn without a human resetting the environment.