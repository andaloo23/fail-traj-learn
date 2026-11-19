# Episode: C0350

## Episode annotation

- Language task: Pick up the plastic ice-cream and put it into the pink bowl.
- Success label: failure
- Outcome evidence: The robot approaches the orange-and-white plastic ice-cream and closes its gripper around it (frames 90–124, wrist_cam and right_base_cam), but subsequently opens and withdraws without carrying it (frames 141–170). At frame 240, left_base_cam and right_base_cam show the ice-cream still on the table outside the pink bowl; wrist_cam shows another approach in progress. An earlier acquisition visibly failed, while the final attempt remains unfinished and completion is not confirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 141 | No |
| 141 | 170 | Yes |
| 170 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 141-170
- Categories: grasp
- Explanation: After closing around the ice-cream, the gripper opens at frames 141–148, closes again around frames 149–155, and opens again before withdrawing empty at frames 163–169 (wrist_cam). The ice-cream shifts slightly but remains on the tabletop rather than being acquired and transported, as confirmed by left_base_cam and right_base_cam at frame 170. These unsuccessful acquisition motions do not accomplish the pickup; the images do not establish a hidden mechanical or perception cause.
- Recovery: Re-localize the ice-cream in its current pose, align the fingers around a secure grasp region, close, and verify retention with a small controlled lift before transporting it to the bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The ice-cream remains on the table, with no visible damage, spill, or disruption to the bowl or nearby red object.
- Resetability: immediate
- Resetability evidence: The target remains accessible on the tabletop, so another aligned grasp can be attempted without environmental resetting or human intervention.