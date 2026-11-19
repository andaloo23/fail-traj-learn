# Episode: C0935

## Episode annotation

- Language task: Move the banana to the pot on the right and sushi to the bowl.
- Success label: failure
- Outcome evidence: In image_primary, the banana is transferred from the bowl to the right-hand pot and remains there after release (frames 30–57). The red-and-white sushi is lifted (frames 76–80) but released outside the bowl (frames 93–99). At frame 159, the sushi remains on the table and the bowl is empty, establishing a visibly unsuccessful sushi transfer rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 93 | No |
| 93 | 103 | Yes |
| 103 | 113 | No |
| 113 | 160 | Yes |

## Failure annotations

### Failure 1

- Frames: 93-103
- Categories: manipulation
- Explanation: In image_primary, the robot opens its gripper while the held sushi is outside the bowl at frames 93–96. The sushi settles on the tabletop beside the bowl at frames 97–102, so the established grasp does not result in the required placement.
- Recovery: Reacquire the sushi, lift it clear of the rim, and position it over the bowl interior before releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The sushi remains on the tabletop, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The sushi is accessible beside the bowl and can be grasped again without environmental intervention.

### Failure 2

- Frames: 113-160
- Categories: grasp, collision
- Explanation: During the renewed acquisition in image_primary, the nearby white utensil is visibly displaced and rotated at frames 113–116. The gripper closes beside the sushi and withdraws without it at frames 121–129, establishing failed acquisition. It subsequently moves within and above the empty bowl through frame 159 while the sushi remains on the table, without a successful reacquisition or transfer.
- Recovery: Withdraw clear of the bowl and utensil, realign the fingers around the sushi, and confirm possession during a short lift before transporting it into the bowl. No human intervention is required for the task retry; the displaced utensil can be restored separately.
- Severity: low
- Severity evidence: The failed grasp leaves the sushi on the table, and the utensil shifts without visible breakage or other damage.
- Resetability: minor_reset
- Resetability evidence: Restoring the displaced utensil to its previous position is a straightforward minor reset; the sushi and both containers remain accessible and usable.