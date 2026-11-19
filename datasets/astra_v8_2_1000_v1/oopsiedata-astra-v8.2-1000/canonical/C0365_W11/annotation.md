# Episode: C0365_W11

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: Provisional for this window: base_image frames 3500–3554 show the gripper engaging the pink bowl area, but frames 3555–3603 show it withdrawing empty while the bowl remains on the table. At frame 3849 the pink bowl is still outside the right red tray; the blue bowl is inside that tray and visible cans are in the upper blue tray. A failed acquisition is visible, while eventual task completion remains unconfirmed. Earlier context is limited to frames 3498–3499, and later execution is not supplied.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 3500 | 3555 | No |
| 3555 | 3604 | Yes |
| 3604 | 3850 | No |

## Failure annotations

### Failure 1

- Frames: 3555-3604
- Categories: grasp
- Explanation: In base_image frames 3555–3582 the gripper begins withdrawing from the pink bowl without lifting it; frames 3588–3603 clearly show the empty gripper separated from the bowl, which remains upright on the table. This establishes unsuccessful acquisition rather than merely unfinished finger closure. The preceding engagement is visible at frames 3500–3554, but its hidden contact mechanics are uncertain. Subsequent small repositioning movements are not independently established as failure.
- Recovery: Re-align the open fingers around an accessible portion of the pink bowl rim, close securely, and verify that the bowl follows a small controlled lift before transporting it to the right tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The bowl remains upright and accessible in base_image frames 3588–3603; no damage, spill, or harmful displacement is visible.
- Resetability: immediate
- Resetability evidence: The failed acquisition leaves the bowl on the tabletop with no environmental restoration required before another attempt.