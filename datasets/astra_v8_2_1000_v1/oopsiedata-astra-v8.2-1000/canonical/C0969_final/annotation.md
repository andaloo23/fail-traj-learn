# Episode: C0969

## Episode annotation

- Language task: put the sushi in the pot
- Success label: failure
- Outcome evidence: The robot handles the wrong object: the wrist view at frames 45–56 distinguishes the orange-and-white sushi on the left from the yellow waffle-textured, mint-ended object between the fingers. Frames 68–89 in left and wrist show the latter being carried to the orange bowl, and frames 93–95 show its release there. The sushi remains on the table and the metal pot remains separate in left at frame 95; this is a visibly task-inconsistent execution, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 26 | No |
| 26 | 96 | Yes |

## Failure annotations

### Failure 1

- Frames: 26-96
- Categories: sequencing_semantic
- Explanation: From frames 26–40, wrist shows the gripper shifting its alignment toward the yellow waffle-textured object while the orange-and-white sushi stays outside the grasp area. Frames 56–78 in wrist and left establish acquisition and transport of that wrong object, with the sushi left behind. The robot then deposits it in the orange bowl at frames 93–95 rather than putting the sushi in the separate metal pot visible in left. This continuous wrong-object operation does not advance the requested task.
- Recovery: Leave the deposited object stable, withdraw the gripper, identify the orange-and-white sushi and metal pot, then grasp the sushi and place it inside the pot; no human intervention is visibly required.
- Severity: low
- Severity evidence: An unrelated object is relocated into a bowl, but neither camera shows damage, spilling, or meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: Returning the misplaced yellow object from the accessible orange bowl to the tabletop is a straightforward reset; the sushi and metal pot remain available and intact.