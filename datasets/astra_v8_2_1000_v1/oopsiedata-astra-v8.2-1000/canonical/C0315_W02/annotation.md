# Episode: C0315_W02

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: Sorting remains incomplete in this observed window: overhead_cam and wrist_cam show the carrot-shaped object left on the table after an empty retreat at frames 422–437 and further unsuccessful acquisition motions at frames 529–645. At frame 699, the robot is approaching the carrot again; no additional bowl placement is visible, and other food-shaped objects remain outside the bowls. This is a provisional window outcome with visible failed attempts, not a final whole-episode judgment; earlier context beyond frames 348–349 and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 422 | No |
| 422 | 438 | Yes |
| 438 | 529 | No |
| 529 | 666 | Yes |
| 666 | 700 | No |

## Failure annotations

### Failure 1

- Frames: 422-438
- Categories: grasp
- Explanation: After closing near the carrot at frames 405–421, the robot lifts away empty while the carrot remains on the table, visible in overhead_cam and wrist_cam at frames 422–437. This establishes failed acquisition rather than merely an unfinished closure; reopening for another approach begins at frame 438.
- Recovery: Reopen, align the fingers around the carrot's body at an appropriate height, and verify a secure grasp with a small lift before transporting it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The carrot remains on the tabletop and neither camera shows damage or a meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The object remains accessible on the table, allowing another attempt without environmental resetting or human intervention.

### Failure 2

- Frames: 529-666
- Categories: grasp
- Explanation: In wrist_cam, the fingers reopen at frames 529–545 without securing the carrot, then repeat closing and reopening near its leafy end at frames 559–585 and 624–645. overhead_cam confirms that the carrot stays on the tabletop; at frames 634–638 it rotates and slides away rather than being lifted. These repeated unsuccessful acquisition motions do not advance sorting. A clearer wrist reorientation and renewed approach begin at frame 666.
- Recovery: Stop repeating the same near-end closure, reassess the carrot's changed pose, and approach across its wider body with sufficient finger clearance; verify retention before moving toward the food bowl. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The visible consequence is unsuccessful acquisition and displacement of the carrot on the table; no damage, spill, or object falling off the table is observed.
- Resetability: immediate
- Resetability evidence: Despite its changed orientation, the carrot remains within the visible tabletop workspace and can be approached again without a human reset.