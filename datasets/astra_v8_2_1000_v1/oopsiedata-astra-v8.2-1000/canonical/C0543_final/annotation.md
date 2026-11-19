# Episode: C0543

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn from the table at frames 33–40 and carries it toward the pot at frames 50–65. After release at frame 70, the corn falls outside the pot and remains on the tabletop at frames 71–72; the pot is empty. This is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 70 | No |
| 70 | 73 | Yes |

## Failure annotations

### Failure 1

- Frames: 70-73
- Categories: manipulation
- Explanation: After carrying the corn to the pot, the robot opens its gripper at frame 70 in right_shoulder_cam, but the corn falls outside the pot and moves across the tabletop at frames 71–72. Established object control did not result in the intended placement; the images do not establish the precise cause of the release error.
- Recovery: Reacquire the corn from the tabletop, align it fully inside the pot opening, and lower it before releasing. No human intervention appears necessary.
- Severity: low
- Severity evidence: The corn lands on the tabletop, with no visible damage, spill, or disruption to other objects in right_shoulder_cam at frames 70–72.
- Resetability: immediate
- Resetability evidence: The corn remains visibly accessible on the table and the pot remains upright and empty; another acquisition and placement attempt requires no environmental reset.