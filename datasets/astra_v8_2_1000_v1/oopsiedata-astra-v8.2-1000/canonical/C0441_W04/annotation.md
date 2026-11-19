# Episode: C0441_W04

## Episode annotation

- Language task: take the small silver cup and pour its contents into the blue bowl
- Success label: failure
- Outcome evidence: Provisional for this window: no pour is completed. In right and top at frames 1050–1075, the gripper withdraws without the silver cup, which retains its red and green contents. The robot subsequently acquires and repositions the blue bowl near the cup (left, right, and top, frames 1175–1350), potentially preparing for another attempt. At frame 1399, right and top still show the contents in the cup and the bowl empty. A failed cup acquisition is visible, but a failed pour is not; eventual completion remains unconfirmed because earlier and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1068 | No |
| 1068 | 1076 | Yes |
| 1076 | 1400 | No |

## Failure annotations

### Failure 1

- Frames: 1068-1076
- Categories: grasp
- Explanation: In right at frames 1068–1075, the fingers pull clear of the silver cup without carrying it; top confirms that the cup remains on the table beside the bowl with its contents retained. This empty withdrawal establishes unsuccessful acquisition rather than a successful lift. The close interaction was already underway at the window boundary, so its earlier history is unavailable; the failure is labeled from the visible empty withdrawal, not from the preceding approach.
- Recovery: Realign the gripper around an accessible cup handle or suitable exterior grasp point, close securely, and verify possession with a small controlled lift before moving above the bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The cup and its contents remain on the tabletop, with no visible spill, damage, or meaningful damage risk from the missed acquisition.
- Resetability: immediate
- Resetability evidence: The cup remains accessible and contains its contents; another acquisition can be attempted without environmental resetting or human intervention.