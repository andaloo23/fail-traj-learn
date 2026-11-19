# Episode: C0177

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is the blue-and-white stuffed toy and the largest bowl is the central white bowl. The robot instead approaches and handles the pink toy on the right (frames 10–40), which lands outside the bowl at frames 41–42. At frame 99, the blue-and-white target remains on the table and the gripper is still engaged with the pink toy. This is visibly wrong-object behavior, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 10 | No |
| 10 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 10-100
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary, the robot directs its approach toward the right pink toy starting at frame 10 rather than the left blue-and-white target. It closes around the pink toy at frames 15–18 but withdraws empty at frames 19–21 while that toy remains on the table, establishing failed acquisition. A subsequent grasp lifts the pink toy at frames 31–40, but it falls or is released outside the white bowl at frames 41–42. The robot then returns to the same wrong toy at frames 46–99, without correcting object selection. This continuous wrong-object sequence does not accomplish the requested transfer.
- Recovery: Safely release the pink toy onto the table, withdraw, and identify the blue-and-white toy on the left. Grasp that target securely, lift it clear of nearby objects, and place it inside the largest white bowl. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The pink toy is displaced and lands on the tabletop, but no damage or meaningful damage risk is visible in image_primary frames 42–99.
- Resetability: immediate
- Resetability evidence: The intended target and largest bowl remain accessible and usable at frame 99; the robot can release the wrong toy and attempt the correct transfer without environmental repair or human resetting.