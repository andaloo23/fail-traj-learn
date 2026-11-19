# Episode: C0441_W05

## Episode annotation

- Language task: take the small silver cup and pour its contents into the blue bowl
- Success label: failure
- Outcome evidence: Provisional for this window: no contents reach the blue bowl. The robot repositions the bowl beside the cup (right and top, frames 1400–1605), but the bowl then tips and rocks on the table before settling upright (left, right, and top, frames 1606–1623). A subsequent cup acquisition is unsuccessful: the gripper withdraws empty while the cup retains its red and green contents (right and top, frames 1713–1725). At frame 1749, right and top still show the contents in the cup and the bowl empty. Earlier execution beyond the two context frames and later execution are unavailable; eventual completion is unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1400 | 1606 | No |
| 1606 | 1624 | Yes |
| 1624 | 1713 | No |
| 1713 | 1726 | Yes |
| 1726 | 1750 | No |

## Failure annotations

### Failure 1

- Frames: 1606-1624
- Categories: grasp
- Explanation: The previously held blue bowl tips away from the fingers and rocks on the tabletop rather than remaining securely controlled during placement (left, right, and top, frames 1606–1622). By frame 1623 it has settled upright beside the cup. This loss of stable retention disrupts preparation of the receiving bowl; no contents are transferred during it.
- Recovery: Let the bowl settle, verify that it is upright and stable, and reposition it with a secure grasp if needed before attempting the pour; no human intervention is visibly required.
- Severity: low
- Severity evidence: The empty bowl rocks on the table and settles upright, with no visible breakage, spill, or other damage.
- Resetability: immediate
- Resetability evidence: The bowl settles upright within reach beside the cup, allowing another attempt without human intervention or environmental resetting.

### Failure 2

- Frames: 1713-1726
- Categories: grasp
- Explanation: After the gripper closes near the silver cup, it pulls away without carrying it (right and top, frames 1713–1725). The cup remains on the table with both colored contents inside, establishing failed acquisition rather than an unfinished closing motion. The earlier approach and alignment are not labeled as failures.
- Recovery: Reopen and align the fingers around an accessible cup handle or exterior grasp point, establish a secure grip, and verify possession with a small controlled lift before positioning the cup over the bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The missed acquisition leaves the cup and its contents on the table, with no visible spill or damage.
- Resetability: immediate
- Resetability evidence: The cup and upright bowl remain accessible, so the robot can reattempt acquisition without a human reset.