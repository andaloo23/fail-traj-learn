# Episode: C0115

## Episode annotation

- Language task: Pack the toys onto the wooden tray.
- Success label: failure
- Outcome evidence: The robot moves the yellow banana-shaped object aside, attempts to acquire the brown plush toy, and subsequently places the pink rabbit on the tray. Frames 584–600 in wrist_cam and overhead_cam show the rabbit released onto the tray. At frame 649 in both cameras, the brown toy remains on the table, so packing the toys is visibly incomplete, not merely unconfirmed. The yellow object's removal may be preparation to clear tray space; its intended inclusion among the toys is ambiguous.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 254 | No |
| 254 | 346 | Yes |
| 346 | 650 | No |

## Failure annotations

### Failure 1

- Frames: 254-346
- Categories: grasp
- Explanation: After closing around the brown toy at frames 243–253, the gripper withdraws without it: wrist_cam frames 254–280 show the toy remaining on the tabletop while the closed gripper moves away, corroborated by overhead_cam. The robot continues empty toward the tray and opens its fingers at frames 337–345 without depositing a toy. This completed acquisition and empty transfer do not advance packing.
- Recovery: Return to the brown toy, realign the open fingers around its body, close, and verify that it lifts with the gripper before transferring it to the tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy remains on the usable tabletop; neither camera shows damage or a meaningful damage risk from the missed acquisition.
- Resetability: immediate
- Resetability evidence: The brown toy remains accessible for another grasp, with no cleanup, repair, or human reset required.