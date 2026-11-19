# Episode: C0141

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot acquires and lifts the wooden spoon, visible in frames 90–130 in image, left_ego_image and wrist_image, then moves it toward the drawer. At frames 209–259, the spoon remains held outside the drawer and the robot stops making visible progress. No placement or release into the drawer is shown; completion is unconfirmed, rather than a visibly failed release or dropped spoon.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 209 | No |
| 209 | 260 | Yes |

## Failure annotations

### Failure 1

- Frames: 209-260
- Categories: task_not_attempted
- Explanation: After transporting the spoon toward the drawer, the robot remains essentially stationary with the spoon still gripped outside it for approximately four seconds, through the end of the episode (frames 209, 230 and 259, image, left_ego_image and wrist_image). This sustained stall does not advance placement; no visible cause or abnormal termination is established.
- Recovery: Reassess the spoon’s position relative to the drawer opening, then continue a collision-free placement and release after the spoon is inside; no human intervention is visibly required.
- Severity: low
- Severity evidence: The spoon remains retained, with no visible damage, dropping or disruption to surrounding objects; the observed consequence is incomplete placement.
- Resetability: immediate
- Resetability evidence: No environmental repair or object repositioning is visibly necessary; the robot can resume from the retained-spoon state without a human reset.