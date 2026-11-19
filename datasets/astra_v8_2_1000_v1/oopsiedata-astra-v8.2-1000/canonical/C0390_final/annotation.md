# Episode: C0390

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: The robot puts both animal toys in the blue bowl (wrist_cam, frames 180 and 430) and the carrot in the green bowl (wrist_cam, frame 615). However, it misses the brown food-shaped object and later puts the orange fruit-shaped object with the toys (wrist_cam, frames 675–705 and 990–1000). At frame 1071, wrist_cam shows the brown object still on the table, the carrot alone in the green bowl, and the orange object mixed with the toys in the blue bowl; overhead_cam corroborates the remaining tabletop object. This is visibly incomplete and incorrect sorting, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 675 | No |
| 675 | 776 | Yes |
| 776 | 930 | No |
| 930 | 1007 | Yes |
| 1007 | 1072 | No |

## Failure annotations

### Failure 1

- Frames: 675-776
- Categories: grasp
- Explanation: During closure, the brown object moves out from between the fingers rather than being acquired (wrist_cam and overhead_cam, frames 675–681). The robot then moves away empty toward the green bowl and opens its fingers there, while the brown object remains on the table (frames 705–775, both cameras). This empty transfer does not sort the object.
- Recovery: Re-localize the brown object, open and center the fingers around its sides, and verify a stable lift before transporting it to the green bowl; no human intervention is needed.
- Severity: low
- Severity evidence: The object remains on the tabletop, with no visible damage or meaningful damage risk; the consequence is a failed acquisition and wasted transfer.
- Resetability: immediate
- Resetability evidence: The brown object remains accessible for another grasp without human resetting.

### Failure 2

- Frames: 930-1007
- Categories: sequencing_semantic
- Explanation: The robot carries the orange fruit-shaped object toward the blue bowl containing the two animal toys, aligns above that bowl, and releases it inside (wrist_cam, frames 930–994; overhead_cam corroborates the placement). Frame 1000 shows the food-shaped object mixed with the toys, contrary to separating food from toys. Acquisition and transport themselves succeed physically.
- Recovery: Retrieve the orange object from the blue bowl and place it in the green bowl with the carrot, then acquire and sort the remaining brown food-shaped object; no human intervention is needed.
- Severity: low
- Severity evidence: The visible consequence is incorrect sorting, without damage to the objects, bowls, or robot.
- Resetability: minor_reset
- Resetability evidence: Returning to a valid sorting state requires a straightforward transfer of the orange object out of the toy bowl; no repair or difficult retrieval is required.