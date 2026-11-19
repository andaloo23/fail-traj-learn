# Episode: C0087

## Episode annotation

- Language task: put the sushi in the pot
- Success label: failure
- Outcome evidence: The orange-and-white sushi remains on the table throughout, including frames 105, 177 and 255 in camera left. Instead, the robot closes near the yellow-and-mint cone-shaped object, retreats empty, and later picks up the wooden letter block. Frames 225–255 in cameras wrist and left show the block transported to and released into the pot. This is visible wrong-object behavior, not merely unconfirmed sushi placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 48 | No |
| 48 | 256 | Yes |

## Failure annotations

### Failure 1

- Frames: 48-256
- Categories: sequencing_semantic, grasp
- Explanation: From frame 48, camera wrist shows the gripper aligning with the yellow-and-mint cone-shaped object rather than the orange-and-white sushi beside it. It closes near the cone at frames 105–112, then withdraws empty at frames 113–125 while both objects remain on the table in camera left, establishing failed acquisition. The robot continues to the pot and opens its empty gripper at frame 177, then approaches and grasps the unrelated wooden letter block at frames 200–225. Frames 235–255 in cameras left and wrist show it carrying that block to the pot and releasing it inside, without moving the sushi. These actions form a continuous task-inconsistent sequence without visible recovery toward the intended object.
- Recovery: Remove the misplaced block from the pot and return it to a clear table location, then identify and grasp the orange-and-white sushi, verify possession, and place it in the pot. No human intervention is visibly required.
- Severity: low
- Severity evidence: The sushi task remains incomplete and an unrelated block is misplaced; no damage, spill or meaningful damage risk is visible in cameras left and wrist through frame 255.
- Resetability: minor_reset
- Resetability evidence: The block must be retrieved from the open, accessible pot and returned to the table; this is a straightforward reset, with no repair or difficult retrieval visibly necessary.