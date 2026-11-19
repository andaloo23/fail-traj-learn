# Episode: C0416

## Episode annotation

- Language task: Stack and pack the cups.
- Success label: failure
- Outcome evidence: In base_image, the robot separates the initially nested cups (frames 81–183) and builds a small stack with two lower cups and one upper cup (frames 250–264). Subsequent handling disrupts that arrangement: cups tip and separate during frames 364–384, and the remaining held cup is released without restoring the stack at frames 414–429. The final view shows scattered cups rather than a completed stack or packed arrangement; this is a visibly unsuccessful attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 364 | No |
| 364 | 385 | Yes |
| 385 | 414 | No |
| 414 | 430 | Yes |

## Failure annotations

### Failure 1

- Frames: 364-385
- Categories: manipulation
- Explanation: In base_image, the right gripper lowers and shifts its held cup while another cup beneath it tips away (frames 364–374). The gripper then opens, leaving its cup to fall onto its side (frames 375–384), disrupting the previously established stack rather than packing the cups.
- Recovery: Reacquire the displaced cups individually, restore stable orientations, and align them for controlled nesting before releasing; human intervention is not necessarily needed if the robot can safely reorient them.
- Severity: low
- Severity evidence: The cups remain on the tabletop with no visible breakage or other damage; the observed consequence is loss of the stacked arrangement.
- Resetability: minor_reset
- Resetability evidence: The displaced and sideways cups require straightforward repositioning or reorientation, but remain accessible on the table.

### Failure 2

- Frames: 414-430
- Categories: manipulation
- Explanation: After moving the remaining held cup toward the other cups, the left gripper opens in base_image at frames 414–423 without establishing a stable stack. As it withdraws at frames 424–429, the released cup tips onto its side, leaving the cups scattered.
- Recovery: Reorient the cups and rebuild a stable stack or nested pack, verifying support and alignment before opening the gripper; human intervention is not inherently required.
- Severity: low
- Severity evidence: The released cup tips on the tabletop without visible damage, and no meaningful damage risk is established by the images.
- Resetability: minor_reset
- Resetability evidence: Returning the newly tipped cup to a stable orientation requires a simple reset; no repair or difficult retrieval is visibly necessary.