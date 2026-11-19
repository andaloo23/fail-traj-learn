# Episode: C0140_W03

## Episode annotation

- Language task: stack the bowls
- Success label: failure
- Outcome evidence: No completed bowl stack is visible: left and top show the pale and turquoise bowls separate at frames 700, 925 and 1049. Instead, the robot carries the orange, green-stemmed object and deposits it in the turquoise bowl (left and right, frames 760–885). It subsequently acquires and moves the turquoise bowl (right and top, frames 975–1049), but stacking remains unconfirmed. This is a provisional window outcome; earlier context beyond frames 698–699 and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 700 | 880 | Yes |
| 880 | 1050 | No |

## Failure annotations

### Failure 1

- Frames: 700-880
- Categories: sequencing_semantic
- Explanation: The orange object remains between the fingers as the arm moves relative to the stationary bowls (right, frames 700–750); left confirms it being carried at frames 760–785. The robot then lowers and releases this unrelated object into the turquoise bowl (left and right, frames 800–879), rather than stacking bowls. This supports wrong-object handling, not a physical grasp failure. The interaction is already underway at the window start and may extend into earlier unseen execution; unlike the preceding prediction's collision-only interpretation, this window establishes controlled transport and placement. Withdrawal begins around frame 880, followed by bowl-directed handling.
- Recovery: Remove the orange object from the bowl and set it safely on a clear tabletop area, then grasp a bowl rim and align the bowls for stacking; no human intervention is visibly required.
- Severity: low
- Severity evidence: An unrelated object is relocated into a bowl, but no breakage, spill or meaningful damage risk is visible.
- Resetability: minor_reset
- Resetability evidence: Returning to the prior clear-bowl state requires a straightforward removal of the orange object; both bowls and the object remain accessible, so this can be done by the robot without a required human reset.