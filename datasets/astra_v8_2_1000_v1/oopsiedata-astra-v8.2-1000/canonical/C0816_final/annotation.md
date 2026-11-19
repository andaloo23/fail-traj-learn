# Episode: C0816

## Episode annotation

- Language task: Open the oven.
- Success label: success but side effects
- Outcome evidence: The initially closed door (frame 0, image and left_ego_image) is pulled outward and downward, visibly separating from the oven body by frames 80–90 and remaining open at frame 178. During the continued pull, the oven body also shifts and rotates on the tabletop (frames 101–162, image), rather than only its door moving. No damage or overturned tabletop objects is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 101 | No |
| 101 | 179 | Yes |

## Failure annotations

### Failure 1

- Frames: 101-179
- Categories: other
- Explanation: While continuing to hold and pull the open door, the robot also displaces and rotates the whole oven on the table. This becomes observable from frame 101 and grows clearer at frames 140, 151 and 162 in image; left_ego_image shows the arm continuing the door interaction through frame 178. Moving the appliance itself is an unintended side effect, although the door has opened.
- Recovery: Stop pulling the appliance, safely release the handle once the door is stable, and reassess its position; a person can restore the oven to its original placement if needed before another attempt.
- Severity: low
- Severity evidence: The oven remains upright on the tabletop, with no visible breakage, falling objects or other meaningful damage; the observed consequence is displacement.
- Resetability: minor_reset
- Resetability evidence: Returning the oven to its original position and orientation requires a straightforward repositioning; no repair or difficult retrieval is visibly necessary.