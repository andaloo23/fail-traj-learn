# Episode: C0759_W05

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisional for this window: the robot lifts and transports the blue toy at frames 1400–1538, then releases it onto the plate at frames 1541–1547 (overhead_cam, wrist_cam). Subsequent low gripper movement disturbs the toys and pushes the plate across the table at frames 1559–1587; the tan toy ends up beside the plate rather than on it. At frame 1749, overhead_cam shows the blue and pink toys on the plate and the tan toy outside it. Thus the observed arrangement fails the task, rather than merely having an unconfirmed placement. Earlier execution and later recovery are not supplied.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1559 | No |
| 1559 | 1589 | Yes |
| 1589 | 1750 | No |

## Failure annotations

### Failure 1

- Frames: 1559-1589
- Categories: collision
- Explanation: After releasing the blue toy, the open gripper continues moving low among the plate and toys instead of clearing them. At frames 1559–1564, wrist_cam shows the blue toy abruptly shifting beside the fingers; at frames 1567–1587, overhead_cam shows the plate sliding across the tabletop while wrist_cam shows the tan toy becoming separated from the plate. This unwanted contact disrupts the completed arrangement and violates the no-collisions requirement. The gripper begins clearing the displaced arrangement by frame 1589.
- Recovery: Lift the gripper vertically clear of the plate and toys, reassess their positions, and reacquire the tan toy from the tabletop before placing it fully inside the rim; use a clearance-preserving withdrawal. No human intervention appears necessary.
- Severity: low
- Severity evidence: The plate and toys are displaced on the tabletop, but no breakage, damage, or meaningful damage risk is visibly established.
- Resetability: immediate
- Resetability evidence: The displaced plate and tan toy remain accessible on the table, allowing another attempt from their current positions without human resetting.