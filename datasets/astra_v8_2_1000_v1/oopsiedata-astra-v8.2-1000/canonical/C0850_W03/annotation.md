# Episode: C0850_W03

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: Sorting remains incomplete in this window. overhead_cam shows repeated attempts around the blue toy, with the orange and brown objects still on the table at frames 700–1000. The blue toy is eventually lifted and carried toward the purple bowl at frames 1008–1049, but release is not visible. wrist_cam at frames 1041–1049 shows a carrot and pink animal toy together in that bowl, rather than separated categories. This is a provisional window outcome: failed acquisitions are visible, while final completion is unconfirmed; earlier context beyond frames 698–699 and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 700 | 974 | Yes |
| 974 | 1050 | No |

## Failure annotations

### Failure 1

- Frames: 700-974
- Categories: grasp
- Explanation: The robot repeatedly closes and reopens its fingers near the blue toy without lifting it. wrist_cam shows the initially closed fingers reopening at frames 733–744 with the toy still on the table, another closure at frames 784–803 followed by reopening at frames 816–830, and further ineffective cycles at frames 849–914 and 920–939. overhead_cam corroborates the toy remaining at the tabletop throughout these retries. This is a continuous unsuccessful acquisition sequence, not merely an unfinished closure. The similar pose in context frames 698–699 suggests continuity across the left window boundary, but the earlier failure onset cannot be independently established here. The interval ends as the final successful acquisition begins at approximately frame 974; subsequent lifting is visible at frames 1008–1018.
- Recovery: Open and lift clear, reassess the toy's position, and align the fingers around a secure part of its body before closing and verifying a lift; then place it in the designated toy bowl. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The retries leave the toy on the tabletop with limited local displacement; neither overhead_cam nor wrist_cam establishes damage or a meaningful damage hazard.
- Resetability: immediate
- Resetability evidence: The toy remains accessible, the bowls remain upright, and no cleanup or environmental repair is needed before a revised grasp attempt.