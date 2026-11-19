# Episode: C0785_W03

## Episode annotation

- Language task: pick up the ductape and put it in the green bowl
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window: top at frames 700, 850, 1000 and 1049 shows both tape rolls outside the empty green bowl. After initial inactivity, the robot approaches the rolls, as visible in left, right and top at frames 842-850 and 950-1025, but no completed pickup or placement is established. This is a provisional window outcome, not a confirmed failed grasp or final episode outcome; earlier context is limited to frames 698-699 and later context is absent.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 700 | 818 | Yes |
| 818 | 1050 | No |

## Failure annotations

### Failure 1

- Frames: 700-818
- Categories: task_not_attempted
- Explanation: In left, right and top at frames 700, 740, 780 and 817, the robot remains near the front of the table with only small pose/viewpoint adjustments and no discernible acquisition attempt or sustained approach to either roll. Both rolls and the bowl remain undisturbed. This approximately four-second period is persistently unproductive; the still posture is also visible in context frames 698-699, though its earlier duration cannot be independently established. The segment ends as the left arm begins the approach visible from frame 818 onward.
- Recovery: Identify the intended duct-tape roll, align and approach it with an open gripper, securely acquire it, and transfer it into the green bowl; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is delayed progress only; left, right and top through frame 817 show no damage, collision or object displacement.
- Resetability: immediate
- Resetability evidence: The rolls and bowl remain available and undisturbed on the table in top at frame 817, so proceeding with an attempt needs no environmental reset.