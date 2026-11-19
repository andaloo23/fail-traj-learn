# Episode: C0945

## Episode annotation

- Language task: put the knife in the cup
- Success label: failure
- Outcome evidence: The robot acquires the orange-handled knife from the plate and lifts it (frames 60–85, left, right and wrist). It carries the knife toward the cup but releases it outside the opening (frames 131–139, left and wrist). At frames 141–147, the knife rests on the countertop beside the plate, not in the upright cup; this is a visibly failed placement rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 131 | No |
| 131 | 148 | Yes |

## Failure annotations

### Failure 1

- Frames: 131-148
- Categories: manipulation
- Explanation: After establishing control of the knife, the robot opens its gripper without inserting the knife into the cup (frames 131–133, wrist and left). The knife falls onto the countertop and settles beside the plate (frames 134–147, wrist and left), leaving the intended placement unsuccessful.
- Recovery: Reacquire the knife by its handle, align it with the cup opening, and lower it into the cup before releasing; verify that the cup supports it. No human intervention is visibly required.
- Severity: low
- Severity evidence: The knife lands on the countertop; no damage, spill, or other meaningful disruption is visible in frames 139–147.
- Resetability: immediate
- Resetability evidence: The knife remains accessible on the countertop and the cup remains upright, allowing another attempt without an environmental reset.