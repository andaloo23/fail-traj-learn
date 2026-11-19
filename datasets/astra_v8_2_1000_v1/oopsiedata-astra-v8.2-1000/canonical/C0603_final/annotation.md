# Episode: C0603

## Episode annotation

- Language task: put the sushi in the pot
- Success label: failure
- Outcome evidence: The orange-and-white sushi remains on the tabletop in left frames 0–191. Instead, the robot closes around the yellow waffle-textured cone-shaped object (wrist frames 65–80), leaves it behind (left and wrist frames 81–85), and then picks up the green-lettered wooden block and releases it into the pot (left and wrist frames 145–191). This is a visibly wrong-object execution, not merely unconfirmed task completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 32 | No |
| 32 | 192 | Yes |

## Failure annotations

### Failure 1

- Frames: 32-192
- Categories: sequencing_semantic, grasp
- Explanation: By frame 32, the approach is directed at the yellow cone-shaped object rather than the adjacent orange-and-white sushi (left and wrist). The fingers close around that unrelated object in wrist frames 65–80, but withdraw empty while it remains on the table in frames 81–85. The robot continues the wrong-object sequence by approaching the lettered block, grasping it in frames 145–160, and carrying and releasing it into the pot in frames 161–191 (left and wrist). Neither operation advances putting the sushi in the pot.
- Recovery: Leave the cone alone, remove the block from the pot and return it to a clear tabletop location, then identify and grasp the orange-and-white sushi and place it in the pot. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The unrelated block is relocated into the pot and the cone acquisition fails, but no damage, spill, or meaningful damage risk is visible in left or wrist frames 81–191.
- Resetability: minor_reset
- Resetability evidence: Returning the block from the open, accessible pot to the tabletop is a straightforward reset; the sushi remains available and no repair or substantial scene restoration is visibly needed.