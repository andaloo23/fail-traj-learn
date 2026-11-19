# Episode: C0373

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn successfully at frames 33–40 and carries it toward the pot at frames 50–70. At frame 71 it releases the corn outside the pot; the corn lands on the tabletop at frames 72–74 and remains there through frame 80. This is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 71 | No |
| 71 | 81 | Yes |

## Failure annotations

### Failure 1

- Frames: 71-81
- Categories: manipulation
- Explanation: In right_shoulder_cam at frame 71, the gripper opens with the corn outside the pot's receiving area. The corn falls onto the tabletop in front of the pot at frames 72–74 rather than into it. The gripper remains empty and the corn stays outside the pot through frame 80.
- Recovery: Regrasp the corn from the tabletop, align it fully over the pot opening, and lower it inside before releasing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The corn lands on the tabletop and remains accessible; no damage, spill, or disruption to other objects is visible in right_shoulder_cam at frames 72–80.
- Resetability: immediate
- Resetability evidence: The corn and pot remain accessible and intact, allowing another attempt directly from the resulting scene without human resetting.