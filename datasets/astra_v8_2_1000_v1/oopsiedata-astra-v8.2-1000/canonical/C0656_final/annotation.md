# Episode: C0656

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn in frames 32–40 and transports it toward the pot in frames 50–69, but releases it outside the pot at frame 70. The corn lands on the tabletop and remains there through frame 78 while the pot is empty. This is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 70 | No |
| 70 | 79 | Yes |

## Failure annotations

### Failure 1

- Frames: 70-79
- Categories: manipulation
- Explanation: In right_shoulder_cam, the previously held corn is released at frame 70 near the pot's front-right edge and falls onto the tabletop rather than into the pot. Frames 71–78 show it settling and remaining outside the empty pot, with no corrective acquisition.
- Recovery: Reacquire the corn from the tabletop, align it fully over the pot opening, and lower it before releasing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The corn falls a short distance onto the tabletop; no damage or disturbance of unrelated objects is visible in right_shoulder_cam frames 70–78.
- Resetability: immediate
- Resetability evidence: The corn remains accessible on the tabletop and the pot stays upright and usable, allowing another attempt without environmental intervention.