# Episode: C0322

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: overhead_cam and wrist_cam show the beige toy released outside the plate at frames 155–167, followed by repeated unsuccessful acquisition cycles, including frames 426–483 and 1027–1045. At frames 1749–1799, the plate remains empty and the toys remain outside it. Thus the episode contains visibly failed attempts, not merely an unconfirmed final placement. No unwanted collision, damage, or abnormal termination is clearly established; proximity to the plate alone does not establish collision.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 155 | No |
| 155 | 168 | Yes |
| 168 | 345 | No |
| 345 | 360 | Yes |
| 360 | 426 | No |
| 426 | 484 | Yes |
| 484 | 534 | No |
| 534 | 566 | Yes |
| 566 | 576 | No |
| 576 | 614 | Yes |
| 614 | 711 | No |
| 711 | 775 | Yes |
| 775 | 839 | No |
| 839 | 861 | Yes |
| 861 | 887 | No |
| 887 | 976 | Yes |
| 976 | 1027 | No |
| 1027 | 1046 | Yes |
| 1046 | 1129 | No |
| 1129 | 1395 | Yes |
| 1395 | 1558 | No |
| 1558 | 1800 | Yes |

## Failure annotations

### Failure 1

- Frames: 155-168
- Categories: manipulation
- Explanation: wrist_cam shows the gripper opening outside the plate at frames 155–160, followed by the beige toy falling onto the tabletop through frame 167; overhead_cam confirms the off-plate landing. The release fails to place the toy on the plate.
- Recovery: Reacquire the toy, verify a retained lift, and position it fully above the plate interior before releasing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy lands on the tabletop without visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible for another attempt without environmental resetting.

### Failure 2

- Frames: 345-360
- Categories: manipulation
- Explanation: Following the second acquisition and movement, wrist_cam shows another opening beside the plate at frames 345–351, with the beige toy exposed below the fingers and resting outside the plate by frame 360. overhead_cam confirms no placement. The release continues across frame 350 rather than ending at that window boundary.
- Recovery: Reacquire the toy and verify clearance above the plate interior before opening the fingers; no human intervention is visibly required.
- Severity: low
- Severity evidence: The unsuccessful release leaves the toy on the tabletop with no visible damage.
- Resetability: immediate
- Resetability evidence: The toy remains reachable and the scene requires no manual reset.

### Failure 3

- Frames: 426-484
- Categories: grasp
- Explanation: After closure at frames 420–425, wrist_cam shows withdrawal and movement toward the plate without a retained toy, followed by reopening at frames 465–480. The beige toy remains on the tabletop in overhead_cam and is clearly outside the open fingers in wrist_cam at frames 480–483.
- Recovery: Realign the fingers around the toy's body and verify acquisition with a small lift before transport; no human intervention is needed.
- Severity: low
- Severity evidence: Acquisition fails without visible damage or harmful displacement.
- Resetability: immediate
- Resetability evidence: The accessible toy can be approached again without resetting the environment.

### Failure 4

- Frames: 534-566
- Categories: grasp
- Explanation: Following closure at frames 525–533, the gripper withdraws without lifting the beige toy. wrist_cam reveals the toy still on the table as the fingers reopen at frames 555–565; overhead_cam shows no transfer onto the plate.
- Recovery: Adjust grasp depth and alignment to enclose the toy, then confirm retention before moving away; no human assistance is visibly necessary.
- Severity: low
- Severity evidence: Only acquisition fails; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The toy remains available for another autonomous attempt.

### Failure 5

- Frames: 576-614
- Categories: grasp
- Explanation: After closing again at frames 566–575, the gripper moves toward the plate empty at frames 576–600. wrist_cam shows reopening and the toy remaining separately beside the plate at frames 612–613, consistent with overhead_cam.
- Recovery: Return with open fingers, establish a verified grasp, and lift clear of the rim before transporting the toy; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Empty transport produces no visible damage or harmful side effect.
- Resetability: immediate
- Resetability evidence: The toy and plate remain accessible without environmental intervention.

### Failure 6

- Frames: 711-775
- Categories: grasp
- Explanation: Following closure at frames 700–710, the robot withdraws and moves toward the plate without carrying the beige toy. wrist_cam shows the empty reopening at frames 765–774, while overhead_cam confirms that the toy remains outside the plate.
- Recovery: Reposition the fingers around the toy's body and verify a retained lift before transport; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The missed acquisition causes no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: Another attempt can begin without resetting the tabletop scene.

### Failure 7

- Frames: 839-861
- Categories: grasp
- Explanation: After closure at frames 837–838, the gripper withdraws without acquiring the toy and reopens. wrist_cam clearly shows the beige toy still on the tabletop at frames 855–860; overhead_cam shows the plate still empty.
- Recovery: Correct finger alignment and height rather than repeating the same closure, and verify retention with a small lift; no human intervention is visibly required.
- Severity: low
- Severity evidence: No damage or harmful side effect is visible.
- Resetability: immediate
- Resetability evidence: The toy remains reachable and no manual reset is needed.

### Failure 8

- Frames: 887-976
- Categories: grasp
- Explanation: Following closure at frames 885–886, the gripper moves away without a retained toy. wrist_cam shows the beige toy outside the fingers at frames 930–945 and clearly separate during reopening at frames 960–975; overhead_cam confirms no placement.
- Recovery: Return with open fingers, enclose the toy's body, and verify that it rises with the gripper before transport; no human assistance is visibly necessary.
- Severity: low
- Severity evidence: The unsuccessful cycle loses task progress but causes no visible damage.
- Resetability: immediate
- Resetability evidence: The toy remains on the accessible tabletop without a need for environmental resetting.

### Failure 9

- Frames: 1027-1046
- Categories: grasp
- Explanation: During closure, wrist_cam shows the beige toy moving out of the finger gap at frames 1027–1028 and remaining outside it at frame 1035. The fingers reopen through frame 1045 without lifting the toy; overhead_cam likewise shows no transfer. Secure prior possession is not established.
- Recovery: Reassess the toy's changed pose, align the fingers across its body, and verify a retained lift; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy shifts on the tabletop without visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The changed pose requires gripper realignment, not an environmental reset.

### Failure 10

- Frames: 1129-1395
- Categories: grasp
- Explanation: After closure, wrist_cam shows movement of the closed gripper while the beige toy remains outside the fingers at frames 1129, 1185 and 1290. Small movements and pauses continue without a retained lift through frame 1380; overhead_cam confirms the empty plate. Opening beginning at frame 1395 leads into realignment at frames 1410–1440 and is treated as recovery rather than extending failure to a window boundary.
- Recovery: Open fully, realign around the toy with clearance from the plate, and verify retention before transport; no human intervention is visibly required.
- Severity: low
- Severity evidence: The extended unsuccessful acquisition causes no visible damage or harmful displacement.
- Resetability: immediate
- Resetability evidence: The toy and plate remain usable and accessible without manual resetting.

### Failure 11

- Frames: 1558-1800
- Categories: grasp
- Explanation: After closure at frames 1545–1557, the robot moves and rotates the closed gripper without acquiring the beige toy, which is visibly outside the fingers in wrist_cam at frames 1620–1665. It then moves away empty through frames 1680–1749 and continues closed-gripper movement through frame 1799; overhead_cam shows no placement. There is no clear renewed acquisition or recovery at frame 1750, so this continuous unsuccessful cycle is not split at the window boundary. Initial occlusion limits precise contact interpretation, and the recording end does not establish abnormal termination.
- Recovery: Stop empty transport, open the fingers, reacquire the toy's position, and verify a secure lift before carrying it above the plate; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The toy remains on the tabletop, with no visible damage or independently established collision.
- Resetability: immediate
- Resetability evidence: The scene remains usable and the toy accessible; a corrected acquisition requires no visible environmental reset.