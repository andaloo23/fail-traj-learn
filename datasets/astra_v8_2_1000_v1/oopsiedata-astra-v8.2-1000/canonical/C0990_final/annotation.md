# Episode: C0990

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn successfully in frames 30–38 and carries it toward the pot in frames 47–63. Upon release in frame 69, the corn falls outside the pot and comes to rest on the tabletop beside its handle in frames 71–73. The pot remains empty; this is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 69 | No |
| 69 | 74 | Yes |

## Failure annotations

### Failure 1

- Frames: 69-74
- Categories: manipulation
- Explanation: After successfully carrying the corn, the robot releases it outside the pot opening in right_shoulder_cam frame 69. The corn falls onto the tabletop to the right of the pot in frames 70–73 rather than remaining inside, so the placement fails.
- Recovery: Reacquire the corn from the tabletop, center it within the pot opening, and lower it into the pot before releasing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The corn lands on the tabletop and the pot stays upright; frames 70–73 show no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The corn remains on the visible tabletop beside the pot, allowing another acquisition and placement attempt without an environmental reset or human intervention.