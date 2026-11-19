# Episode: C0021

## Episode annotation

- Language task: Pick up the pen with the right hand and the cap with the left hand, then insert the cap onto the pen.
- Success label: failure
- Outcome evidence: The supplied task ambiguously says “pen cap” for the right hand as well as “cap” for the left; the visible long pen and short cap support the interpretation above. Frames 193–350 in right_wrist and left_wrist show acquisition of the separate pieces, followed by bringing them together. At frames 569–613, left_wrist and right_wrist show the cap released without remaining attached to the pen, ending on the table. Frames 655–727 show the pen also back on the table and the grippers repositioning. Through frame 1399, no assembled pen is visible; this is a visibly unsuccessful capping attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 569 | No |
| 569 | 613 | Yes |
| 613 | 727 | No |
| 727 | 1400 | Yes |

## Failure annotations

### Failure 1

- Frames: 569-613
- Categories: grasp
- Explanation: At frame 569 in left_wrist, the cap-holding fingers begin opening before a secure pen-cap connection is established. Frames 591–605 in right_wrist and left_wrist show the short cap tipping away and falling rather than staying on the pen; by frame 613 it lies separately on the table. The release loses control of the cap and defeats this capping attempt.
- Recovery: Locate the cap again, regrasp it with the left hand, align its opening with the pen tip, and verify secure seating before releasing it; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The small cap falls onto the work surface, with no visible breakage or damage to other objects.
- Resetability: immediate
- Resetability evidence: The cap remains in the accessible central workspace and can be reacquired without human resetting.

### Failure 2

- Frames: 727-1400
- Categories: task_not_attempted
- Explanation: After repositioning, the robot remains nearly stationary above the unassembled pieces for the rest of the episode. Comparing frames 727, 900, 1100 and 1399 in left_wrist, right_wrist and top shows only small pose changes, without reacquisition or renewed insertion during this sustained interval.
- Recovery: Reassess the visible locations and orientations of the two pieces, then resume a deliberate acquisition and alignment sequence; no human intervention is visibly required.
- Severity: low
- Severity evidence: The sustained lack of progress leaves the task unfinished but produces no visible damage or concrete damage risk.
- Resetability: immediate
- Resetability evidence: The parts remain on the work surface and the scene is usable for another attempt without physical reset.
