# Episode: C0762

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the cardboard box.
- Success label: failure
- Outcome evidence: The first acquisition leaves the animal on the table while the gripper rises empty (external and wrist, frames 359–370). A later grasp lifts and carries it toward the box (external and wrist, frames 657–674), but it is released outside the box and settles on the adjacent tabletop (frames 852–868). The robot subsequently moves empty toward the box and withdraws; the animal remains outside at frame 1274 in external. This is a visibly unsuccessful placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 359 | No |
| 359 | 452 | Yes |
| 452 | 852 | No |
| 852 | 868 | Yes |
| 868 | 1275 | Yes |

## Failure annotations

### Failure 1

- Frames: 359-452
- Categories: grasp
- Explanation: Following finger closure near the animal, the gripper lifts away empty while the animal remains on the table (external and wrist, frames 359–370), then remains above it without acquiring it through frame 451. A renewed descent begins at frame 452.
- Recovery: Reopen and realign the fingers around a sufficiently substantial part of the animal, descend, close, and verify possession with a short lift; no human intervention is needed.
- Severity: low
- Severity evidence: The failed acquisition leaves the soft toy on the tabletop without visible damage or disruption.
- Resetability: immediate
- Resetability evidence: The animal remains accessible in its original area; no environmental resetting is needed.

### Failure 2

- Frames: 852-868
- Categories: manipulation
- Explanation: After established possession and transport, the gripper opens while the animal is still beside rather than over the box (external and wrist, frames 852–859). The animal falls onto the tabletop outside the box and settles there by frame 867, defeating the intended placement.
- Recovery: Reacquire the animal, lift it clear of the box rim, center it over the opening, and lower it inside before releasing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The soft animal lands on the table; no damage to the animal, box, or surroundings is visible.
- Resetability: immediate
- Resetability evidence: The animal remains on an accessible tabletop beside the upright box and can be grasped again without a human reset.

### Failure 3

- Frames: 868-1275
- Categories: sequencing_semantic
- Explanation: Rather than reacquiring the animal left beside the box, the robot continues empty: it shifts position around frames 938–957, moves the empty gripper toward and over the box in frames 1028–1048, and withdraws in frames 1130–1148. External shows the animal remaining outside throughout, including frame 1274; wrist confirms the empty fingers during the continued motion. This continuation does not complete or recover the failed placement.
- Recovery: Return to the animal’s observed tabletop position and execute a verified grasp and placement into the box; no human intervention is required by the visible state.
- Severity: low
- Severity evidence: The continuation leaves the task incomplete without visible damage or harmful contact.
- Resetability: immediate
- Resetability evidence: The box and animal remain available for another attempt; no scene repair or rearrangement is necessary.
