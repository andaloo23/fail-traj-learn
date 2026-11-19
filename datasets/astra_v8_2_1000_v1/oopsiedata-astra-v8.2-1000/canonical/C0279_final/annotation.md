# Episode: C0279

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left stuffed toy is blue-and-white and the largest bowl is the central white bowl. The robot instead handles the pink toy on the right (frames 15–21, 42–51, and 73–94). At frames 96–99, the pink toy rests on the tabletop in front of the white bowl, while the intended blue-and-white toy remains unmoved on the left. The observed task visibly fails rather than merely having unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 9 | No |
| 9 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 9-100
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary frame 9, the gripper approaches the right-hand pink toy rather than the requested left blue-and-white toy, then contacts and moves it in frames 15–20. The pink toy returns to the table as the gripper lifts away empty at frame 21, establishing failed retention independently of the wrong-object selection. Further attempts remain directed at the pink toy, including movement in frames 42–51 followed by an empty gripper at frame 52. Frames 81–93 show sustained lifting of that wrong toy, followed by its return to the tabletop outside the bowl in frames 94–99. This continuous wrong-object behavior never advances relocation of the intended toy.
- Recovery: Leave or safely release the pink toy on a clear tabletop area, then identify and grasp the left blue-and-white toy, verify retention, and carry it over the white bowl before releasing inside. No human intervention is visibly required.
- Severity: low
- Severity evidence: The wrong plush toy is displaced and repeatedly returned to the tabletop, but image_primary frames 21, 52, and 99 show no visible damage, overturned bowls, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The intended blue-and-white toy and white bowl remain accessible and unchanged through image_primary frame 99; the task can be reattempted without a necessary environmental reset or human intervention.
