# Episode: C0576

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the cardboard box.
- Success label: failure
- Outcome evidence: The robot acquires and lifts the stuffed animal (external and wrist, frames 518–533), then carries it toward the box (frames 613–635). After release and withdrawal (frames 718–730), the animal is draped across the box’s left rim rather than placed inside. This unsuccessful placement remains visible in external at frames 825, 1000 and 1274; completion is not merely hidden or unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 718 | No |
| 718 | 730 | Yes |
| 730 | 1275 | No |

## Failure annotations

### Failure 1

- Frames: 718-730
- Categories: manipulation
- Explanation: After successfully transporting the animal, the robot releases it while it is still across the left edge of the box (external and wrist, frames 718–724). As the gripper withdraws, the animal remains draped on the rim with much of its body outside instead of settling into the box (external, frames 725–729). This is a failed placement after established object control, not a missed initial grasp.
- Recovery: Reacquire the animal around its body, lift it clear of the rim, center it over the box opening, then lower and release it inside; verify that it rests in the box. No human intervention appears necessary.
- Severity: low
- Severity evidence: The soft toy remains supported at the box edge; no damage, overturned box, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The animal and upright box remain accessible, so the robot can attempt corrective placement without environmental resetting or human intervention.