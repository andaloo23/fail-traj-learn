# Episode: C0113

## Episode annotation

- Language task: Pour a bowl of M&Ms into a bowl of skittles.
- Success label: failure
- Outcome evidence: The blue bowl contains yellow M&M packets (right_wrist, frames 100–110), and the green bowl contains red Skittles packets (left_wrist, frames 214–230). The robot lifts, transfers between grippers, and tilts the blue bowl over the green bowl. Some packets enter the green bowl, but at least one lands outside it during frames 265–273 (head, right_wrist). One packet remains in the blue bowl at frame 304 (left_wrist), so complete transfer is not confirmed; the episode shows a partial pour with visible spillage, not merely an unseen outcome.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 265 | No |
| 265 | 283 | Yes |
| 283 | 305 | No |

## Failure annotations

### Failure 1

- Frames: 265-283
- Categories: manipulation
- Explanation: During the pour, a yellow M&M packet passes outside the receiving green bowl and settles on the tabletop beside it (head and right_wrist, frames 265–273). The robot holds the tilted source bowl through frame 282 without correcting this spill; renewed tipping begins at frame 283. Bowl control is retained, but the transfer does not keep all contents inside the intended destination.
- Recovery: Reposition the source bowl so its pouring edge is securely over the green bowl, finish transferring the remaining packet, and retrieve the spilled packet into the green bowl. Human intervention is not evidently required if the packet is safely reachable.
- Severity: low
- Severity evidence: A packaged candy item spills onto the tabletop; no torn packaging, broken bowl, or other damage is visible in head or right_wrist at frames 273–283.
- Resetability: minor_reset
- Resetability evidence: Returning the spilled packet to a bowl is a straightforward minor reset; the bowls and packet remain accessible on or above the table, with no repair or substantial cleanup visibly needed.