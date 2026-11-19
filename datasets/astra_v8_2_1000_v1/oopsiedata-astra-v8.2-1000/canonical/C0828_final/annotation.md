# Episode: C0828

## Episode annotation

- Language task: Pack the cups with a single arm.
- Success label: failure
- Outcome evidence: In base_image, all three cups initially sit outside the box (frame 0). The pale cup topples and rolls away during frames 22–30, and a subsequent closing motion leaves the right blue cup on the table (frames 40–55). Repeated hovering and approach–retreat motions follow without packing any cup; both blue cups and the sideways pale cup remain outside the box at frame 135. This is visible unsuccessful behavior, not merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 22 | No |
| 22 | 28 | Yes |
| 28 | 40 | No |
| 40 | 55 | Yes |
| 55 | 76 | No |
| 76 | 136 | Yes |

## Failure annotations

### Failure 1

- Frames: 22-28
- Categories: other
- Explanation: In base_image frames 22–27, the pale cup tips out of the cluster and falls onto its side rather than being acquired or packed. This occurs as the gripper moves near and away from the cluster (frames 21–23), but the precise initiating contact is not resolved; established possession and a dropped grasp are not visible.
- Recovery: Locate the sideways cup, approach with clearance from the other cups, and acquire it securely before transferring it to the box; no human intervention is visibly required.
- Severity: low
- Severity evidence: The cup rolls on the tabletop without visible breakage, spilled contents, or damage to other objects.
- Resetability: minor_reset
- Resetability evidence: Returning the cup to its initial standing arrangement requires a simple repositioning on the accessible tabletop; no repair or difficult retrieval is indicated.

### Failure 2

- Frames: 40-55
- Categories: grasp
- Explanation: In base_image frames 40–46, the fingers close near the upper end of the right blue cup without acquiring it. They reopen during frames 48–52 and withdraw empty in frames 53–55 while the cup remains in place, confirming a failed acquisition.
- Recovery: Reposition the open fingers around the cup body at a suitable height, close securely, and verify that the cup moves with the gripper before transporting it; human intervention is not needed.
- Severity: low
- Severity evidence: The attempted grasp leaves the blue cup standing and visibly intact; no damage is shown.
- Resetability: immediate
- Resetability evidence: The target remains accessible in its previous position, allowing another attempt without environmental intervention.

### Failure 3

- Frames: 76-136
- Categories: task_not_attempted
- Explanation: In base_image frames 76–135, the gripper repeatedly approaches and retreats above the blue cups without acquiring or transferring one, including repeated near-identical passes at frames 76–86, 100–110, and 123–135. Taken together, these sustained repetitions are unproductive rather than a single ordinary alignment pause.
- Recovery: Stop repeating the ineffective motions, reassess the cup locations and grasp height, and execute a deliberate acquisition followed by a verified transfer to the box; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: These motions make no packing progress but cause no additional visible object displacement or damage.
- Resetability: immediate
- Resetability evidence: This segment introduces no further environmental change; the cups remain available for a revised attempt without a reset.