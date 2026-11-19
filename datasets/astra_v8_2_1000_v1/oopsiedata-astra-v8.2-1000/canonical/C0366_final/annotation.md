# Episode: C0366

## Episode annotation

- Language task: Push the Displayport cable into the cable holder on the white block.
- Success label: failure
- Outcome evidence: The robot approaches the cable and holder, but no cable is visibly seated in the holder. In wrist and top, frames 227, 430, 625 and 890 show the cable remaining beside the white block while the robot repeatedly changes pose nearby; front shows the block remaining upright. Frames 918–923 still show the cable outside the holder. Completion is not confirmed, and the repeated unproductive motions are visibly observable rather than inferred from the recording ending.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 324 | No |
| 324 | 345 | Yes |
| 345 | 405 | No |
| 405 | 924 | Yes |

## Failure annotations

### Failure 1

- Frames: 324-345
- Categories: grasp
- Explanation: After the fingers close beside the cable at frames 316–323 in wrist, the robot lifts away with the fingers together but without the cable during frames 324–344. The cable stays on the surface beside the block in wrist and top, establishing an empty acquisition rather than merely unfinished finger closure.
- Recovery: Reopen the gripper, align the cable between both fingertips, and verify acquisition with a small lift before moving toward the holder; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The missed acquisition prevents progress, with no visible damage, spill or overturned fixture in front or top.
- Resetability: immediate
- Resetability evidence: The cable remains accessible beside the upright block; no environmental intervention is required before another attempt.

### Failure 2

- Frames: 405-924
- Categories: task_not_attempted
- Explanation: Following renewed approach, the robot enters sustained repetitive, unproductive cycling beside the cable and holder. Wrist shows recurring withdrawal poses at frames 430, 625 and 890 and low poses beside the cable at frames 490, 695 and 923; top shows no corresponding cable transfer into the holder. These repeated cycles do not establish acquisition or advance insertion, rather than being a single slow approach or brief pause.
- Recovery: Stop repeating the same motion, re-localize the cable and an open holder slot, acquire and verify control of the cable, then align and gently press it into the slot; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is prolonged failure to advance the task; the cable, holder and white block show no observable damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The cable remains on the accessible work surface and the block remains upright, so another attempt needs no scene reset.
