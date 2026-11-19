# Episode: C0251_W02

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: This is a provisional outcome for the supplied window. In overhead_cam and wrist_cam, the blue toy is released near the plate edge at frames 403–410 and lands on the table by frame 413. The robot retrieves it and successfully places it on the plate at frames 578–590. The pink toy remains on the table at frame 699 after an empty grasp closure and reopening at frames 658–684. Thus completion is not visible, and local failed attempts are visible; later completion remains unknown. Earlier context beyond frames 348–349 is unavailable as image evidence.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 403 | No |
| 403 | 414 | Yes |
| 414 | 658 | No |
| 658 | 673 | Yes |
| 673 | 700 | No |

## Failure annotations

### Failure 1

- Frames: 403-414
- Categories: manipulation
- Explanation: After transporting the held blue toy, the robot opens its gripper at the plate edge (frames 403–406, wrist_cam). The toy falls outside the plate and settles on the table (frames 408–413, overhead_cam and wrist_cam), so this placement fails. This is an unsuccessful release location rather than an established accidental loss of grip.
- Recovery: Regrasp the blue toy, move it fully over the plate interior with clearance from the rim and beige toy, and lower it before releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The soft toy lands on the tabletop beside the plate; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The toy remains accessible on the table for an autonomous retry without environmental intervention.

### Failure 2

- Frames: 658-673
- Categories: grasp
- Explanation: In wrist_cam, the fingers close to the right of the pink toy during frames 658–670 rather than enclosing its body. The completed closure leaves the toy on the tabletop, and the fingers begin reopening at frame 673; overhead_cam likewise shows no acquisition. Reopening and subsequent adjustment are recovery, not continued failed acquisition.
- Recovery: Open the fingers fully, recenter them around the pink toy’s body, then close and verify possession before lifting; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition leaves the toy on the table with no visible damage or harmful displacement.
- Resetability: immediate
- Resetability evidence: The target remains accessible in essentially the same tabletop location, so another aligned grasp requires no human reset.