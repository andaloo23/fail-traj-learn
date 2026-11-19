# Episode: C0322_W02

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisionally, the task is not achieved in this window: overhead_cam shows the toys remaining outside the plate at frames 350, 480, 612 and 699. wrist_cam shows repeated closing and reopening near the beige toy without successful transfer. No unwanted collision is clearly established. The opening at frames 348–357 is consistent with the preceding report's unsuccessful attempt, but these images alone do not establish prior possession or an off-plate drop. Earlier acquisition context and later completion are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 426 | No |
| 426 | 484 | Yes |
| 484 | 534 | No |
| 534 | 566 | Yes |
| 566 | 576 | No |
| 576 | 614 | Yes |
| 614 | 700 | No |

## Failure annotations

### Failure 1

- Frames: 426-484
- Categories: grasp
- Explanation: Following closure at frames 414–425 in wrist_cam, the robot moves the closed gripper away from the acquisition position without carrying the beige toy; overhead_cam shows the toy remaining on the tabletop outside the plate. The gripper subsequently opens at frames 465–480, revealing the toy still outside it in wrist_cam. This is an unsuccessful acquisition, not an established carried-object placement failure.
- Recovery: Reposition the open fingers around the beige toy's body, close securely, and verify that the toy rises with the gripper before transporting it above the plate; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The toy remains on the tabletop, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible and the environment requires no visible resetting before another attempt.

### Failure 2

- Frames: 534-566
- Categories: grasp
- Explanation: After another closure at frames 521–533 in wrist_cam, the gripper withdraws without lifting the beige toy, which remains on the table in overhead_cam. Reopening through frames 544–562 exposes the toy still on the tabletop in wrist_cam, confirming another failed acquisition rather than successful transport.
- Recovery: Adjust the grasp position and finger height to enclose the toy rather than closing beside or above it, then verify retention with a small lift; human intervention is not visibly required.
- Severity: low
- Severity evidence: Only acquisition fails; no damage or displacement into an inaccessible location is visible.
- Resetability: immediate
- Resetability evidence: The beige toy remains available for an autonomous retry without environmental intervention.

### Failure 3

- Frames: 576-614
- Categories: grasp
- Explanation: The gripper closes again at frames 566–575, then moves toward the plate at frames 576–594 without the beige toy, which remains outside the plate in overhead_cam. wrist_cam shows the empty gripper opening at frames 598–612 while the toy remains beside the plate. The empty transport does not advance toy placement.
- Recovery: Return to the toy with open fingers, establish and visually verify a retained grasp, then lift clear of the rim and release only above the plate interior; no human assistance is visibly necessary.
- Severity: low
- Severity evidence: The unsuccessful grasp and empty transport cause no visible damage or harmful side effect.
- Resetability: immediate
- Resetability evidence: The scene remains usable and the toy accessible; no manual reset is established as necessary.