# Episode: C0746

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: success but suboptimal
- Outcome evidence: In base_image, the green can is left in the upper blue tray by frame 2700, both cans are there by frame 4600, and both bowls are stacked in the right red tray after gripper withdrawal at frame 6200; the completed arrangement persists through frame 6671. Three unsuccessful can acquisitions precede completion: empty transfers are visible at frames 900–1100, 1700–1800, and 3400–3600 while the respective target remains on the table. No definite damage or harmful side effect is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 786 | No |
| 786 | 1121 | Yes |
| 1121 | 1581 | No |
| 1581 | 1824 | Yes |
| 1824 | 3285 | No |
| 3285 | 3700 | Yes |
| 3700 | 6672 | No |

## Failure annotations

### Failure 1

- Frames: 786-1121
- Categories: grasp
- Explanation: In base_image, withdrawal from the green can begins around frame 786 following acquisition motions; at frames 900–1100, the gripper is over the upper tray without the can, which remains on the tabletop. The empty transfer continues across the window boundary at frame 1050. The interval ends when withdrawal to resume task-directed work begins around frame 1121; the exact transition is less clear in the selected visual checks.
- Recovery: Return to the green can, realign around its body, and verify that it moves with a small lift before transporting it; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The can remains on the tabletop, with no established new damage or spill; its visibly dented condition already exists at frame 0.
- Resetability: immediate
- Resetability evidence: The can remains accessible for another grasp without human intervention or environmental resetting.

### Failure 2

- Frames: 1581-1824
- Categories: grasp
- Explanation: In base_image, the gripper withdraws from the multicolored can around frame 1581 without retaining it. Frames 1700–1800 show the empty gripper over the upper tray while both cans remain on the table. This unsuccessful transfer continues beyond frame 1750, ending around the start of retraction and renewed approach at frame 1824; the exact recovery transition is approximate.
- Recovery: Reapproach the can at its current position, align the fingers around its body, and confirm retention with a small lift before transferring it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The target changes position slightly but remains on the table; no spill, new damage, or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The displaced can is still accessible, so a new acquisition can proceed without resetting the scene.

### Failure 3

- Frames: 3285-3700
- Categories: grasp
- Explanation: In base_image, the gripper closes beside the remaining multicolored can and begins empty withdrawal around frame 3285. Frames 3400–3600 show continued movement over the upper tray while that can remains on the tabletop. The failure continues across frame 3500 rather than ending at the window boundary. By frame 3700, the gripper has withdrawn clear and subsequent frames show renewed approach; this endpoint is approximate because the selected checks do not pinpoint the transition from empty placement motions to recovery.
- Recovery: Return to the remaining tabletop can, correct the grasp alignment, and verify secure acquisition before transferring it while keeping clear of the already placed green can; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The missed target remains on the table, and the green can remains within its destination tray despite some repositioning; no spill or new damage is established.
- Resetability: immediate
- Resetability evidence: Both cans remain accessible and the tray remains usable, so another attempt requires no environmental reset.