# Episode: C0301_W04

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: Provisional for this window: sorting is not completed. Frames 1050, 1201, and 1350 in wrist_cam show toys and food-shaped objects remaining outside the bowls. Gripper-closing motions are followed by empty withdrawals at frames 1158–1189 and 1311–1335, visible across overhead_cam and wrist_cam. At frame 1399 in overhead_cam, the robot is again near the tabletop objects, with no completed placement visible. These include visibly failed acquisitions rather than only unconfirmed completion; earlier execution beyond the supplied context and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1158 | No |
| 1158 | 1190 | Yes |
| 1190 | 1311 | No |
| 1311 | 1336 | Yes |
| 1336 | 1400 | No |

## Failure annotations

### Failure 1

- Frames: 1158-1190
- Categories: grasp
- Explanation: Following finger-closing motions near the tabletop object cluster at frames 1125–1144 in wrist_cam, the robot withdraws empty beginning at frame 1158. Frames 1167–1189 in overhead_cam show the fingers moving away and lifting without an object; wrist_cam subsequently reveals the objects still on the table. The exact acquisition target is partly obscured, so no specific object identity or hidden cause is assigned. Task-directed repositioning resumes at frame 1190.
- Recovery: Reposition above a clearly identified object, align the fingers around a graspable portion, and verify a secure lift before transferring it to the appropriate bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The acquisition produces no visible placement, damage, spill, or meaningful damage risk; the bowls remain upright.
- Resetability: immediate
- Resetability evidence: The objects remain accessible on the tabletop, allowing another attempt without an environmental reset or human intervention.

### Failure 2

- Frames: 1311-1336
- Categories: grasp
- Explanation: Frames 1308–1310 in wrist_cam show the fingers closing near the pink toy. Beginning at frame 1311, the gripper moves away without acquiring it; frames 1320–1335 in overhead_cam show an empty raised gripper while the pink toy remains on the table, corroborated by wrist_cam. No secure possession or drop is established. Repositioning toward the objects resumes at frame 1336.
- Recovery: Reapproach the pink toy with the fingers centered around its body at an appropriate height, close, and confirm retention during a short lift before transporting it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy remains on the tabletop with no visible damage or harmful disturbance to the surrounding scene.
- Resetability: immediate
- Resetability evidence: The failed acquisition leaves the toy accessible for another attempt without resetting the environment.