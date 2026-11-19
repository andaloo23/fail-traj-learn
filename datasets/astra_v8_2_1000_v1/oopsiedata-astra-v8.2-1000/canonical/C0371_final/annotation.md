# Episode: C0371

## Episode annotation

- Language task: Stack the green cup into the purple cup.
- Success label: failure
- Outcome evidence: In exterior_cam, the cups begin separately upright at frame 0. The robot repeatedly contacts the green cup but leaves it tipped on the table rather than transporting it into the purple cup (frames 80, 217, 394, and 515). At frame 599 the green cup remains on its side, separated from the upright purple cup. This is a visibly unsuccessful acquisition sequence, not merely an unconfirmed final insertion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 67 | No |
| 67 | 87 | Yes |
| 87 | 198 | No |
| 198 | 237 | Yes |
| 237 | 385 | No |
| 385 | 428 | Yes |
| 428 | 505 | No |
| 505 | 523 | Yes |
| 523 | 583 | No |
| 583 | 593 | Yes |
| 593 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 67-87
- Categories: grasp
- Explanation: In exterior_cam frames 67-80, the green cup tips out from beneath the fingers and settles sideways without being securely acquired; the purple cup remains untouched. The unsuccessful acquisition leaves the target needing reorientation.
- Recovery: Reassess the cup's sideways pose, grasp its exposed body securely, and right it before lifting; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The cup tips onto the clear tabletop; no spill, breakage, or meaningful damage is visible.
- Resetability: minor_reset
- Resetability evidence: Returning to the original upright setup requires only righting the accessible green cup.

### Failure 2

- Frames: 198-237
- Categories: grasp
- Explanation: In exterior_cam frames 198-217, the green cup tips and remains on the table while the gripper separates from it; frames 233-236 show the empty gripper withdrawing. This renewed acquisition does not retain the target.
- Recovery: Approach the cup using its current pose and verify a secure grasp before lifting or translating; human assistance is not required by the visible state.
- Severity: low
- Severity evidence: The green cup remains on the tabletop without visible damage or spilled contents.
- Resetability: minor_reset
- Resetability evidence: A straightforward righting and repositioning of the cup restores the initial setup; no retrieval or repair is needed.

### Failure 3

- Frames: 385-428
- Categories: grasp
- Explanation: In exterior_cam frames 385-394, the gripper pulls clear without the green cup, which rolls away across the table. By frames 420-427 it lies sideways farther from the purple cup, confirming unsuccessful acquisition rather than transport.
- Recovery: Let the cup settle, reacquire its position, and grasp it without pushing it farther toward the table edge; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The cup rolls on the table but does not fall or visibly sustain damage.
- Resetability: minor_reset
- Resetability evidence: The cup remains accessible and needs only repositioning and righting for a fresh upright attempt.

### Failure 4

- Frames: 505-523
- Categories: grasp
- Explanation: In exterior_cam frames 505-515, the gripper moves away empty after contacting the green cup; the cup stays sideways in the same tabletop area through frame 523. The acquisition has not secured the target.
- Recovery: Reopen and align the fingers around the cup body rather than withdrawing before possession is established; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt leaves the cup on the table with no visible damage or additional harmful consequence.
- Resetability: immediate
- Resetability evidence: Another grasp can be attempted directly from the existing accessible sideways pose; this miss introduces no necessary environmental reset.

### Failure 5

- Frames: 583-593
- Categories: grasp
- Explanation: In exterior_cam frames 583-590, the gripper again separates empty while the green cup settles on its side. It remains separate from the purple cup, so the preceding contact has not produced a retained acquisition.
- Recovery: Reassess finger placement and secure the cup before lifting, then orient it upright and align it over the purple cup; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The cup remains on the tabletop without visible breakage, spill, or damage.
- Resetability: immediate
- Resetability evidence: The target remains accessible for a revised grasp without a required human reset.