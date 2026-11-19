# Episode: C0242

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: No toy is left on the plate. overhead_cam and wrist_cam frames 58–66 show an unsuccessful acquisition of the blue toy, followed by repeated unproductive withdrawals. Frames 765–801 show the blue toy retained and transported over the plate, but frames 802–849 show it carried away and released onto the tabletop. wrist_cam frames 855–870 confirm the blue and tan toys outside the plate; overhead_cam frame 899 shows the plate still empty. This is visibly unsuccessful placement, not merely unconfirmed completion. No unwanted collision or abnormal termination is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 60 | No |
| 60 | 67 | Yes |
| 67 | 147 | No |
| 147 | 321 | Yes |
| 321 | 386 | No |
| 386 | 475 | Yes |
| 475 | 550 | No |
| 550 | 638 | Yes |
| 638 | 802 | No |
| 802 | 850 | Yes |
| 850 | 900 | No |

## Failure annotations

### Failure 1

- Frames: 60-67
- Categories: grasp
- Explanation: Following finger closure near the blue toy, the gripper withdraws empty during frames 60–66. wrist_cam frames 58–66 and overhead_cam frames 65–66 show the toy remaining on the tabletop rather than being lifted. The precise reason for the failed acquisition is not visible.
- Recovery: Realign the fingers around a graspable portion of the blue toy and verify retention with a short lift before transport; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy remains on the table with no visible damage or disruptive collision.
- Resetability: immediate
- Resetability evidence: The toy remains accessible, and no environmental resetting is required.

### Failure 2

- Frames: 147-321
- Categories: task_not_attempted
- Explanation: After approaching the tan toy, the empty gripper reverses away at frames 147–148 and repeatedly moves between the workspace and robot base without acquisition or placement. overhead_cam and wrist_cam frames 165, 210, 240, 270, 300, and 315 show repeated excursions with the toys and plate unchanged. This sustained unproductive movement exceeds an ordinary alignment pause; a renewed approach begins at frame 321.
- Recovery: Stop the repeated excursions and execute a deliberate collision-free approach to one toy, followed by a verified grasp and transport to the plate; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is lost progress; no damage or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The toys and plate remain available in their tabletop positions, requiring no physical reset.

### Failure 3

- Frames: 386-475
- Categories: task_not_attempted
- Explanation: After approaching the blue toy in frames 375–385, the robot withdraws empty from frame 386 and moves away toward its base, as overhead_cam and wrist_cam frames 390–435 show. It then waits with small adjustments away from the targets through frame 474. This abandoned approach and sustained inactivity do not advance placement; a completed grasp attempt is not clearly established. A renewed approach begins at frame 475.
- Recovery: Return to a selected toy with obstacle clearance, align the fingers before closing, and verify possession before transporting it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: No object damage, disruptive contact, or meaningful damage risk is visible; the consequence is lost task progress.
- Resetability: immediate
- Resetability evidence: The tabletop arrangement remains accessible and usable without cleanup or repositioning.

### Failure 4

- Frames: 550-638
- Categories: task_not_attempted
- Explanation: Following another approach near the blue toy in frames 540–549, the robot withdraws empty from frame 550. overhead_cam and wrist_cam frames 555–615 show movement away toward the base without a retained object, followed by waiting through frame 637. This is another abandoned approach with sustained absence of productive action, not a clearly established completed grasp failure. Movement back toward the workspace begins at frame 638.
- Recovery: Resume a deliberate approach to one toy, correct finger alignment, and verify a secure lift before moving toward the plate; no human intervention is visibly required.
- Severity: low
- Severity evidence: The plate remains empty and progress is lost, but no damage or unwanted collision is established.
- Resetability: immediate
- Resetability evidence: No scene component needs resetting; the toys remain accessible for another attempt.

### Failure 5

- Frames: 802-850
- Categories: manipulation
- Explanation: After retaining the blue toy and bringing it over the plate, the robot carries it away from frame 802, increasing its distance from the plate through frames 810–840 in overhead_cam. wrist_cam confirms continued possession during transport, followed by release outside the plate at frames 848–849. Established object control therefore ends in an incorrect placement.
- Recovery: Reacquire the blue toy from the tabletop, lift clear of neighboring toys, center it over the plate interior, and lower before releasing; verify placement before handling the remaining toys. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The blue toy lands on the tabletop with no visible damage or established collision with another object.
- Resetability: immediate
- Resetability evidence: wrist_cam frames 855–870 show the displaced toy still accessible on the tabletop, allowing another attempt without human resetting or cleanup.