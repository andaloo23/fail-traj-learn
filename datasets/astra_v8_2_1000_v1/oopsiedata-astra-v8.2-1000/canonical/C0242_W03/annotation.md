# Episode: C0242_W03

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisional for this window: the robot acquires the blue toy and carries it over the plate (overhead_cam and wrist_cam, frames 753–800), but subsequently carries it away and releases it onto the tabletop rather than the plate (frames 802–850). wrist_cam frames 855–870 show the blue and tan toys outside the plate; overhead_cam frame 899 shows the plate still empty. This is a visibly unsuccessful placement, not merely unconfirmed completion. No unwanted collision is clearly established. Earlier execution beyond the two context frames is unavailable, and the window boundary does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 700 | 802 | No |
| 802 | 850 | Yes |
| 850 | 900 | No |

## Failure annotations

### Failure 1

- Frames: 802-850
- Categories: manipulation
- Explanation: After successfully retaining the blue toy and bringing it over the plate, the robot moves it away again from frame 802, visibly increasing its distance from the plate through frames 810–840 in overhead_cam. wrist_cam confirms continued possession during this transport. At frames 844–849 the fingers open and the toy falls onto the tabletop outside the plate. Thus established object control ends in an incorrect placement rather than advancing the task. The earlier brief lateral adjustments above and beside the plate are not independently treated as failures.
- Recovery: Reacquire the blue toy from its new tabletop position, lift with clearance from the neighboring toy, move over the plate interior, and lower before releasing; verify placement before approaching the remaining toys. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The toy is released onto the tabletop and the plate remains empty; no damage, unwanted contact with another object, or meaningful damage risk is visibly established.
- Resetability: immediate
- Resetability evidence: The displaced blue toy remains on the accessible tabletop, as wrist_cam frames 855–870 show, so another acquisition can be attempted without human resetting or cleanup.