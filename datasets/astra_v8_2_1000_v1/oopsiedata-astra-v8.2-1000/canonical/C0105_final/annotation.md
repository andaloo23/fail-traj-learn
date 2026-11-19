# Episode: C0105

## Episode annotation

- Language task: Pour a bowl of M&Ms into a bowl of skittles.
- Success label: failure
- Outcome evidence: The blue bowl contains yellow M&Ms packets and the green bowl contains red Skittles packets (frame 180, right_wrist and left_wrist). Some M&Ms packets are poured into the green bowl at frames 565–579 (head, left_wrist), but the transfer is incomplete: one packet remains in the blue bowl and another remains on the table at frame 701 (left_wrist, right_wrist). The blue bowl is also dropped during handling at frames 326–337 and 685–697 (head). This is a visibly partial, unsuccessful transfer rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 326 | No |
| 326 | 349 | Yes |
| 349 | 606 | No |
| 606 | 685 | Yes |
| 685 | 698 | Yes |
| 698 | 702 | No |

## Failure annotations

### Failure 1

- Frames: 326-349
- Categories: grasp
- Explanation: The previously held blue bowl escapes the grippers, falls onto the table, and bounces, spilling an M&Ms packet outside the bowl (frames 326–337, head, left_wrist, right_wrist). This interrupts transport before the bowl reaches the Skittles bowl; the precise reason for losing retention is not visible.
- Recovery: Reacquire the bowl securely and retrieve the spilled packet before resuming the transfer; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The bowl and packaged candy land on the tabletop with no visible breakage or other damage.
- Resetability: minor_reset
- Resetability evidence: Returning the spilled packet to the upright blue bowl requires a straightforward pickup; all objects remain accessible on the table.

### Failure 2

- Frames: 606-685
- Categories: manipulation
- Explanation: After transferring several packets, the robot rotates and moves the blue bowl away from the green bowl while an M&Ms packet remains inside (frames 606–670, head and left_wrist). The withdrawal leaves the requested bowl-to-bowl transfer incomplete; the earlier spilled packet also remains on the table (right_wrist).
- Recovery: Reposition the securely held bowl above the green bowl and carefully adjust its tilt to transfer the remaining packet, then recover the tabletop packet; human intervention is not visibly required.
- Severity: low
- Severity evidence: The observed consequence is incomplete transfer, without visible damage or a meaningful additional damage risk.
- Resetability: immediate
- Resetability evidence: The remaining packet is still in the held bowl, so the pouring action can be reattempted without an environmental reset; the earlier tabletop spill is assessed separately.

### Failure 3

- Frames: 685-698
- Categories: grasp
- Explanation: The blue bowl separates from the gripper above the tabletop, falls, and rocks before settling upright with a packet still inside (frames 685–697, head, left_wrist). This is another loss of controlled retention rather than a supported placement.
- Recovery: Regrasp the settled bowl securely and complete the remaining transfer, using a supported placement before releasing it afterward; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The bowl lands on the table and remains intact, with no visible additional spill or damage.
- Resetability: immediate
- Resetability evidence: The bowl settles upright within reach with its remaining packet inside, permitting another acquisition without manual resetting.
