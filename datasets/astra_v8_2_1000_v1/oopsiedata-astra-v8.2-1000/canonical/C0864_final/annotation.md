# Episode: C0864

## Episode annotation

- Language task: Push the Displayport cable into the cable holder on the white block.
- Success label: failure
- Outcome evidence: The cable remains on the work surface rather than in the holder. In front and top, frames 0, 430, 520 and 890 show the cable lying in front of the white block; wrist frames 392–407 and 880–890 show the holder empty. The robot makes two empty-handed approaches to the holder after acquisition attempts. This is a visibly unsuccessful attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 25 | No |
| 25 | 494 | Yes |
| 494 | 545 | No |
| 545 | 891 | Yes |

## Failure annotations

### Failure 1

- Frames: 25-494
- Categories: grasp
- Explanation: After closing near the cable, the gripper begins withdrawing at frame 25 and rises toward the holder through frames 55–124 without carrying it; top and wrist show the cable remaining on the surface. The robot subsequently makes repeated movements above and beside the block without inserting any cable (front and wrist, frames 159–493). Wrist frames 392–407 clearly show the empty holder and the cable below it. The unsuccessful acquisition prevents these movements from advancing insertion; no hidden cause is established.
- Recovery: Return to the visible cable, align the fingers around an accessible cable section, acquire it, and verify that it moves with the gripper before approaching the holder; human intervention is not visibly needed.
- Severity: low
- Severity evidence: The cable and holder remain intact, with no visible damage or meaningful damage risk; the task simply does not progress.
- Resetability: immediate
- Resetability evidence: The cable remains accessible on the work surface and the block stays upright, so another acquisition attempt needs no environmental reset.

### Failure 2

- Frames: 545-891
- Categories: grasp
- Explanation: Following the return to the cable and another closing motion (wrist, frames 520–544), the robot begins moving away again at frame 545 without lifting the cable. Top and wrist frames 576–641 show the cable still lying on the surface while the arm approaches the block. It repeats empty-handed movements near the holder through frame 890; wrist frames 737–890 show no cable seated in the holder. This repeats the failed acquisition rather than completing insertion.
- Recovery: Stop repeating the holder approach, return to the cable, adjust the grasp location and finger alignment, and confirm acquisition visually before transporting and pressing the cable into a holder slot; no human intervention is visibly required.
- Severity: low
- Severity evidence: No cable damage, holder damage, or disruptive side effect is visible; the consequence is another unsuccessful task attempt.
- Resetability: immediate
- Resetability evidence: The cable remains on the accessible work surface and the holder remains upright and usable, allowing a retry without manual resetting.