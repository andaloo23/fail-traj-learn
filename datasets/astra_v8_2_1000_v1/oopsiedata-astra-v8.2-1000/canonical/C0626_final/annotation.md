# Episode: C0626

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: The robot places the carrot and orange-shaped food into the purple bowl (frames 118 and 265, wrist_cam), the blue toy into the green bowl (frame 444, wrist_cam), and the brown food into the purple bowl (frames 730–733, wrist_cam). However, it releases the pink rabbit beside rather than inside the green bowl (frames 605–614, overhead_cam and wrist_cam). The rabbit remains outside at frame 780 in both cameras, so sorting is visibly incomplete, not merely unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 605 | No |
| 605 | 614 | Yes |
| 614 | 781 | No |

## Failure annotations

### Failure 1

- Frames: 605-614
- Categories: manipulation
- Explanation: After successfully carrying the pink rabbit, the robot opens its gripper with the toy positioned outside the green bowl (frames 605–610, wrist_cam). The rabbit is left on the tabletop beside the bowl as the gripper withdraws (frames 613–614, overhead_cam and wrist_cam), failing the intended placement.
- Recovery: Regrasp the rabbit, position its body fully above the green bowl interior, lower it and release, then verify containment; no human intervention is needed.
- Severity: low
- Severity evidence: The rabbit remains on the tabletop beside the upright bowl; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The rabbit remains accessible for another pick-and-place attempt, with no cleanup, repair or human reset required.