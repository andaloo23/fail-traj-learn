# Episode: C0315_W06

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: Completion is not visible in this window: overhead_cam at frames 1750, 1775 and 1799 shows the orange fruit-shaped item still outside both bowls, with no sorting transfer. wrist_cam shows fingers opening and closing near it without visible acquisition and transport. The label is provisional for this window; earlier execution beyond frames 1748–1749 is unavailable, and the window ending does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1750 | 1800 | Yes |

## Failure annotations

### Failure 1

- Frames: 1750-1800
- Categories: task_not_attempted
- Explanation: overhead_cam shows essentially unchanged arm positioning and no transfer throughout frames 1750–1799, while wrist_cam shows repeated finger opening and closing near the orange item, including frames 1750–1757, 1775–1782 and 1787–1799. This repeated unproductive motion does not advance sorting; it does not establish a dropped object or a completed failed lift. Context frames 1748–1749 show similar positioning, but the earlier duration and onset cannot be independently established from those two frames. The behavior remains unresolved at the window edge and may continue beyond it.
- Recovery: Reassess the item's position and reposition the gripper rather than repeating the same finger motion; confirm a secure acquisition before transporting it to the food bowl. No visible condition requires human intervention.
- Severity: low
- Severity evidence: The visible consequence is lack of sorting progress; neither overhead_cam nor wrist_cam shows damage, spilling or a meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The item remains accessible on the tabletop and the bowls remain upright; no environmental reset or human intervention is visibly needed before another attempt.