# Episode: C0766

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: success but side effects
- Outcome evidence: In image_primary, the robot acquires the left blue-and-white stuffed toy and lifts it in frames 18–24, then transports it to the largest, white bowl. Frames 35–38 show the toy inside the bowl with the gripper open. During placement, the robot also displaces and substantially tips the bowl in frames 28–34; it returns upright at a shifted position by frame 35.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 28 | No |
| 28 | 35 | Yes |
| 35 | 39 | No |

## Failure annotations

### Failure 1

- Frames: 28-35
- Categories: collision
- Explanation: In image_primary frames 28–34, the gripper and carried toy encounter the white bowl's rim during placement, pushing the bowl sideways and tipping it substantially rather than clearing the rim. The bowl's displacement and tilt are visible, although the exact contacting component is partly obscured.
- Recovery: Relieve contact with the rim, allow the bowl to settle upright, then reposition the toy above the opening with sufficient clearance before lowering and releasing it; human intervention is not evidently needed.
- Severity: low
- Severity evidence: The bowl tips and shifts but remains on the table and returns upright by frame 35; no breakage, spill, or damage is visible.
- Resetability: immediate
- Resetability evidence: The bowl remains accessible on the tabletop and settles upright, so the robot can continue placement without a human environmental reset.