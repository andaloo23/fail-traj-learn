# Episode: C0500

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn in frames 38–44 and carries it toward the pot in frames 54–70. It releases the corn at frame 76, but the corn falls outside the pot and settles on the tabletop in frames 77–82. This is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 76 | No |
| 76 | 83 | Yes |

## Failure annotations

### Failure 1

- Frames: 76-83
- Categories: manipulation
- Explanation: In right_shoulder_cam frame 76, the gripper releases the previously held corn near the pot's front edge; the corn falls onto the tabletop rather than into the pot in frames 77–80. By frame 82, the corn remains outside and the pot is empty, establishing failed placement.
- Recovery: Reacquire the corn from the tabletop, position it fully over the pot opening, and lower it inside before releasing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The corn falls a short distance onto the tabletop and remains accessible; no damage or meaningful damage risk is visible in right_shoulder_cam frames 77–82.
- Resetability: immediate
- Resetability evidence: The corn rests on the clear tabletop beside the intact pot, allowing another acquisition and placement attempt without environmental repair or human resetting.