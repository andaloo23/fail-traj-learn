# Episode: C0495

## Episode annotation

- Language task: Pick basketball and place in blue bowl.
- Success label: failure
- Outcome evidence: In exterior_cam, the robot lifts the basketball (frames 70–115), but releases it onto the table rather than into the blue bowl (frames 117–124). Further lifts also end with the ball back on the table (frames 382–390 and 513–525). At frame 599 the basketball remains outside the bowl beneath the gripper; this is visible failure to complete placement, not merely an occluded or unconfirmed outcome.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 117 | No |
| 117 | 126 | Yes |
| 126 | 382 | No |
| 382 | 393 | Yes |
| 393 | 427 | No |
| 427 | 436 | Yes |
| 436 | 513 | No |
| 513 | 528 | Yes |
| 528 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 117-126
- Categories: manipulation
- Explanation: After visibly carrying the basketball, the robot opens its gripper away from the bowl in exterior_cam frame 117; the ball falls, bounces, and rolls on the tabletop in frames 118–125. This release fails the intended placement. Repositioning toward the ball begins at frame 126.
- Recovery: Reacquire the basketball, transport it over the bowl opening, and lower it before releasing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The ball stays on the table, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The basketball remains accessible on the clear tabletop and can be reacquired without environmental intervention.

### Failure 2

- Frames: 382-393
- Categories: manipulation
- Explanation: Following another visible lift and carry, the gripper releases the basketball outside the bowl in exterior_cam frames 382–385. The ball settles on the table through frame 392 instead of being placed in the bowl; subsequent gripper repositioning begins at frame 393.
- Recovery: Regrasp the ball and align it above the blue bowl before opening the gripper; human intervention is not visibly needed.
- Severity: low
- Severity evidence: Only unsuccessful placement and tabletop displacement are visible; neither the ball nor surrounding objects show damage.
- Resetability: immediate
- Resetability evidence: The ball remains on an accessible portion of the table, allowing another attempt without a scene reset.

### Failure 3

- Frames: 427-436
- Categories: grasp
- Explanation: After lowering around the basketball in exterior_cam frames 423–426, the gripper rises empty in frames 427–432 while the basketball remains on the tabletop. This establishes unsuccessful acquisition rather than an unfinished closing action. A renewed approach starts at frame 436.
- Recovery: Open the fingers, center them around the basketball at an appropriate height, close securely, and verify retention during a short lift; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition leaves the ball on the table without visible damage or harmful contact.
- Resetability: immediate
- Resetability evidence: No environmental change needs correction before retrying the grasp.

### Failure 4

- Frames: 513-528
- Categories: manipulation
- Explanation: The robot visibly holds the ball in exterior_cam frames 480–512, then opens its gripper outside the bowl at frame 513. The basketball falls and rolls toward the foreground through frame 527, again undoing acquisition without achieving placement. The robot begins following it at frame 528.
- Recovery: Track the ball until it settles, reacquire it, and carry it to the bowl before releasing at low height; human intervention is not visibly required.
- Severity: low
- Severity evidence: The ball rolls across the tabletop but does not visibly fall off or damage anything.
- Resetability: immediate
- Resetability evidence: The ball remains on the table within the robot's subsequent approach area, with no cleanup or manual reset visibly necessary.