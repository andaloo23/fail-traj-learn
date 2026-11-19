# Episode: C0650

## Episode annotation

- Language task: Pick up NIST rod and insert into corresponding hole on the NIST board.
- Success label: success but side effects
- Outcome evidence: Frames 13–19 in side and wrist show acquisition and transport of the rod toward the visible hole, followed by lowering at frames 21–25. During the prolonged insertion attempt, the board shifts across the table (side, frames 25–80). At frames 103–108 the fingers open and the rod settles farther into the hole; it remains upright without finger support through frame 125 in wrist and side, supporting completed insertion despite the board displacement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 26 | No |
| 26 | 102 | Yes |
| 102 | 126 | No |

## Failure annotations

### Failure 1

- Frames: 26-102
- Categories: manipulation
- Explanation: After the rod is brought to the hole, the robot continues holding it at nearly unchanged exposed depth while the board shifts leftward across the table (side, frames 26, 40, 65, and 80; wrist shows little change in rod depth). This prolonged contact displaces the board rather than visibly completing insertion. The rod only settles farther when the fingers begin opening at frames 102–104; the images do not establish the underlying cause of the resistance.
- Recovery: Stop pushing when the board moves, relieve contact pressure, and reassess rod-to-hole alignment before a gentle insertion retry. Human intervention is appropriate if the board needs repositioning or securing before continued contact.
- Severity: low
- Severity evidence: The board is displaced but remains on the table, and neither side nor wrist shows breakage, dropped objects, or other meaningful damage.
- Resetability: minor_reset
- Resetability evidence: Returning the shifted board to its original working position is a straightforward reset; no repair or difficult object retrieval is visibly required.