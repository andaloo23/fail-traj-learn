# Episode: C0090

## Episode annotation

- Language task: Stack and pack the cups.
- Success label: failure
- Outcome evidence: In base_image, the robot separates the initially nested cups (frames 212–358), builds a small pyramid (frames 548–562), and then begins nesting them again (frames 658–815). Packing is not completed: the last cup is released beside, rather than onto, the other cups (frames 872–887), and two separate cup groups remain as both grippers withdraw (frame 905). This is a visible unsuccessful final placement, not merely unconfirmed completion at the recording boundary.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 872 | No |
| 872 | 906 | Yes |

## Failure annotations

### Failure 1

- Frames: 872-906
- Categories: manipulation
- Explanation: In base_image, the left gripper opens at frame 872 with its held cup offset beside the existing nested cups, then withdraws empty (frames 880–887). The released cup remains separate through frame 905, so this placement does not finish packing all cups together.
- Recovery: Reacquire the separate cup, lift it clear of the table, align its opening over the existing nested cups, and lower it gently before releasing; no human intervention appears necessary.
- Severity: low
- Severity evidence: The cups remain on the tabletop with no visible breakage, spill, or meaningful damage risk; the consequence is incomplete packing.
- Resetability: immediate
- Resetability evidence: The separate cup and existing nested cups remain accessible to the robot, so another placement attempt requires no environmental reset or human intervention.