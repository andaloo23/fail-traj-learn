# Episode: C0251

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: success but suboptimal
- Outcome evidence: All three toys are ultimately placed on the plate: the beige toy is released by frame 240, the blue toy is successfully placed by frames 585–600 after an unsuccessful placement, and the pink rabbit is released onto the plate by frame 1545 after repeated failed attempts (overhead_cam and wrist_cam). Frames 1665–1799 show all three remaining on the plate with the empty gripper withdrawn. Earlier unsuccessful releases and acquisitions establish inefficiency; no unwanted collision or damage is clearly established by the supplied views.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 403 | No |
| 403 | 414 | Yes |
| 414 | 658 | No |
| 658 | 673 | Yes |
| 673 | 804 | No |
| 804 | 820 | Yes |
| 820 | 995 | No |
| 995 | 1015 | Yes |
| 1015 | 1120 | No |
| 1120 | 1127 | Yes |
| 1127 | 1279 | No |
| 1279 | 1301 | Yes |
| 1301 | 1361 | No |
| 1361 | 1365 | Yes |
| 1365 | 1440 | No |
| 1440 | 1447 | Yes |
| 1447 | 1800 | No |

## Failure annotations

### Failure 1

- Frames: 403-414
- Categories: manipulation
- Explanation: The robot opens its fingers while holding the blue toy outside the plate interior at frames 403–405 in wrist_cam. By frames 412–413, overhead_cam and wrist_cam show the released toy on the tabletop beside the plate, establishing an unsuccessful placement rather than an unexplained loss of grip.
- Recovery: Regrasp the toy, move it fully over the plate interior with clearance from the rim and beige toy, and lower it before releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The soft toy lands on the tabletop without visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible beside the plate for another attempt without environmental intervention.

### Failure 2

- Frames: 658-673
- Categories: grasp
- Explanation: At frames 658–672, wrist_cam shows the fingers closing beside the pink rabbit rather than enclosing its body. The completed closure leaves the rabbit on the tabletop; reopening at frames 673–675 and the empty fingers at frame 690 confirm failed acquisition, corroborated by overhead_cam.
- Recovery: Open and recenter the fingers around the rabbit’s body, then verify possession with a controlled lift before transport; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition leaves the toy on the table without visible damage or harmful displacement.
- Resetability: immediate
- Resetability evidence: The rabbit remains reachable and requires no manual repositioning or scene reset.

### Failure 3

- Frames: 804-820
- Categories: manipulation
- Explanation: After carrying the pink rabbit toward the plate, the robot opens its fingers outside the plate interior at frames 804–805 in wrist_cam. The rabbit falls at frame 810 and rests on the tabletop at frames 818–819 in overhead_cam and wrist_cam, so the placement does not achieve its goal.
- Recovery: Reacquire the rabbit, lift it clear of the rim, move it fully over an available area of the plate, and lower it before release; no human intervention is needed.
- Severity: low
- Severity evidence: The soft toy lands on the tabletop with no visible damage or significant hazard.
- Resetability: immediate
- Resetability evidence: The rabbit remains accessible beside the plate, allowing an autonomous retry without resetting the environment.

### Failure 4

- Frames: 995-1015
- Categories: grasp
- Explanation: During closure beginning at frame 995, the fingers displace and rotate the pink rabbit instead of securing it, visible by frame 1005 in wrist_cam. The completed closure at frames 1013–1014 leaves it on the tabletop; reopening from frame 1015 exposes it still outside the plate, also visible in overhead_cam.
- Recovery: Open the fingers and realign around the rabbit’s body with clearance from the plate rim, then verify retention with a small lift; no human intervention is needed.
- Severity: low
- Severity evidence: The rabbit is displaced locally, with no visible damage to the toy, plate, or robot.
- Resetability: immediate
- Resetability evidence: The displaced rabbit remains within reach and needs no environmental reset.

### Failure 5

- Frames: 1120-1127
- Categories: grasp
- Explanation: At frames 1120–1126, wrist_cam shows another closure beside the rabbit without securing it. Reopening from frame 1127 and empty withdrawal visible at frame 1140 establish failed acquisition; overhead_cam confirms the rabbit remains on the tabletop outside the plate.
- Recovery: Reopen and center both fingers around the rabbit’s body away from the rim, then confirm acquisition before transport; no human intervention is needed.
- Severity: low
- Severity evidence: The unsuccessful attempt leaves the rabbit on the table without visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The target remains accessible and the scene remains usable without intervention.

### Failure 6

- Frames: 1279-1301
- Categories: grasp
- Explanation: The fingers close alongside the pink rabbit and plate rim during frames 1279–1300 without acquiring the toy. Reopening at frames 1301–1305 in wrist_cam reveals the rabbit still outside the plate, corroborated by overhead_cam. Rim proximity alone does not establish an unwanted collision.
- Recovery: Withdraw slightly, align around the rabbit’s body rather than the narrow space beside the rim, and check retention before lifting toward the plate; no human intervention is needed.
- Severity: low
- Severity evidence: The rabbit remains outside the plate without visible damage to any scene component.
- Resetability: immediate
- Resetability evidence: The rabbit and plate remain reachable and usable, requiring no manual scene reset.

### Failure 7

- Frames: 1361-1365
- Categories: grasp
- Explanation: Following a partial lift visible at frames 1350–1360, the rabbit separates from the fingers at frame 1361 and returns to the tabletop outside the plate by frames 1362–1364 in wrist_cam and overhead_cam. Retention fails; whether the separation was a slip or an intentional release is not established.
- Recovery: Reacquire the rabbit securely around its body, verify a stable lift, and move fully over the plate before lowering and releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The soft toy returns to the tabletop without visible damage or a significant hazard.
- Resetability: immediate
- Resetability evidence: The rabbit remains accessible for another attempt, with no cleanup or manual repositioning necessary.

### Failure 8

- Frames: 1440-1447
- Categories: grasp
- Explanation: At frames 1440–1446, wrist_cam shows the fingers closing beside the pink rabbit near the plate rim without securing it. Reopening from frame 1447 and empty withdrawal by frame 1455 confirm failed acquisition, while overhead_cam shows the rabbit still outside the plate.
- Recovery: Reposition the open fingers around the rabbit’s body with rim clearance, confirm retention with a small lift, and transport it over the plate before release; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition causes no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The rabbit remains reachable beside the plate, so another attempt requires no environmental reset or human intervention.