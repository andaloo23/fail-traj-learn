# Episode: C0322_W03

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisionally for this window, no toy is placed on the plate. overhead_cam shows the empty plate and toys remaining outside it at frames 700, 774, 969 and 1049; wrist_cam shows repeated unsuccessful acquisition cycles near the beige toy. These are visible failed attempts, not merely unconfirmed completion. No unwanted environmental collision is clearly established. Earlier episode context beyond frames 698–699 and later completion are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 700 | 711 | No |
| 711 | 775 | Yes |
| 775 | 839 | No |
| 839 | 861 | Yes |
| 861 | 887 | No |
| 887 | 976 | Yes |
| 976 | 1027 | No |
| 1027 | 1046 | Yes |
| 1046 | 1050 | No |

## Failure annotations

### Failure 1

- Frames: 711-775
- Categories: grasp
- Explanation: After closing near the beige toy at frames 700–710 in wrist_cam, the robot withdraws and moves toward the plate without carrying it at frames 711–755. overhead_cam shows the toy remaining on the tabletop; reopening at frames 757–774 in wrist_cam confirms the empty acquisition. The movement therefore does not transfer a toy.
- Recovery: Reposition the open fingers around the toy's body, close at an appropriate height, and verify retention with a small lift before transport; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy remains on the table, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible, and no environmental intervention is needed before another attempt.

### Failure 2

- Frames: 839-861
- Categories: grasp
- Explanation: Following closure at frames 827–838 in wrist_cam, the gripper withdraws without acquiring the beige toy and opens again through frame 860. wrist_cam clearly reveals the toy still on the tabletop at frames 850–860, consistent with overhead_cam; no placement occurs.
- Recovery: Adjust finger alignment and depth around the toy rather than repeating the same closure, then verify a retained lift before moving to the plate; human intervention is not visibly required.
- Severity: low
- Severity evidence: The failed acquisition causes no visible damage or harmful side effect.
- Resetability: immediate
- Resetability evidence: The toy and plate remain available for another attempt without a manual reset.

### Failure 3

- Frames: 887-976
- Categories: grasp
- Explanation: After the closure at frames 875–886, the gripper moves away empty during frames 887–955 while the beige toy remains beside the plate in overhead_cam. wrist_cam shows the toy outside the closed fingers and then clearly separate as the fingers reopen at frames 956–975. This is failed acquisition and empty movement, not a demonstrated drop from a retained grasp.
- Recovery: Return with open fingers, select a grasp enclosing the toy's body, and confirm that it rises with the gripper before transporting it clear of the plate rim; no human assistance is visibly needed.
- Severity: low
- Severity evidence: Only task progress is lost; neither camera shows damage.
- Resetability: immediate
- Resetability evidence: The toy remains on the accessible tabletop and the scene needs no visible resetting.

### Failure 4

- Frames: 1027-1046
- Categories: grasp
- Explanation: During the next closure, the beige toy moves out of the finger gap at frames 1027–1029 in wrist_cam and remains outside the closed gripper beside the plate. The robot then reopens through frame 1045 without lifting it; overhead_cam likewise shows no transfer. The images establish failed acquisition but not prior secure possession or a hidden mechanical cause.
- Recovery: Reassess the toy's changed pose, approach with fingers spanning its body, and verify acquisition with a small lift before transport; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The toy shifts on the tabletop but shows no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The changed pose can be addressed by repositioning the gripper; the toy remains accessible without environmental intervention.