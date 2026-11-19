# Episode: C0759_W03

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisional for this window: the tan toy is carried toward the plate and released onto it at frames 852–856, beside the pink toy (overhead_cam, wrist_cam). The blue toy is not acquired during a subsequent attempt: the gripper withdraws empty at frames 976–995 while it remains on the table. Another approach follows, but placement of the blue toy is not visible by frame 1049 (overhead_cam, wrist_cam). Thus completion is unconfirmed, with one visibly failed acquisition established. Earlier context beyond frames 698–699 and later execution are unavailable; the window boundary does not establish termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 700 | 976 | No |
| 976 | 997 | Yes |
| 997 | 1050 | No |

## Failure annotations

### Failure 1

- Frames: 976-997
- Categories: grasp
- Explanation: Following finger closure at frames 961–975, the gripper lifts away without the blue toy starting at frame 976; separation becomes clear through frames 983–995 while the toy remains on the tabletop (overhead_cam, wrist_cam). This completed acquisition attempt fails to transport the toy toward the plate. Opening the fingers for another approach begins at frame 997.
- Recovery: Open and realign the fingers around the blue toy’s body, acquire it, and verify retention with a small lift before transporting it above the plate with clearance from the rim and other toys; no human intervention appears necessary.
- Severity: low
- Severity evidence: The toy remains on the tabletop, with no visible damage or meaningful risk of damage from the missed acquisition.
- Resetability: immediate
- Resetability evidence: The blue toy remains accessible for another attempt; no environmental resetting or human intervention is required.