# Episode: C0396

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn from the table in frames 32–40 and carries it toward the pot in frames 50–66. On release at frame 71, the corn falls outside the pot and lands on the table in frames 72–76. The final frame shows the corn outside the empty pot, establishing a visibly failed placement rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 71 | No |
| 71 | 77 | Yes |

## Failure annotations

### Failure 1

- Frames: 71-77
- Categories: manipulation
- Explanation: After successfully carrying the corn, the robot opens its gripper at frame 71 in right_shoulder_cam, but the corn falls outside the pot and settles on the tabletop in frames 72–76. This release fails to place the controlled object in the intended container.
- Recovery: Regrasp the corn from the table, align it fully within the pot opening, and lower it before releasing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The corn lands on the tabletop near the pot; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The corn remains accessible on the table and the pot remains upright, allowing another attempt without environmental resetting.