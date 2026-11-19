# Episode: C0015

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn in frames 31–38 and carries it toward the pot in frames 49–66. After release, the corn falls outside the pot in frame 67 and rests on the tabletop in frames 68–69 while the pot remains empty. This is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 67 | No |
| 67 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 67-70
- Categories: manipulation
- Explanation: After established control and transport of the corn, the placement fails: right_shoulder_cam frame 67 shows the open gripper and corn falling outside the pot, and frames 68–69 show it resting on the table in front of the empty pot. The images do not establish the precise cause of the failed release placement.
- Recovery: Reacquire the corn from the tabletop, align it fully inside the pot opening, lower it before releasing, and verify that it remains in the pot; no human intervention appears necessary.
- Severity: low
- Severity evidence: The corn lands on the tabletop; no damage, spill, or disruption of unrelated objects is visible in right_shoulder_cam frames 67–69.
- Resetability: immediate
- Resetability evidence: The corn remains exposed on the tabletop and the pot remains upright and usable, allowing another acquisition and placement attempt without an environmental reset.