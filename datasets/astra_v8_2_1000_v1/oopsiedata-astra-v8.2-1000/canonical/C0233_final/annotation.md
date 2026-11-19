# Episode: C0233

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot grasps and lifts the wooden spoon (frames 71–100, wrist_image and left_ego_image), then carries it toward the open drawer. At frames 172–180, wrist_image shows the spoon leaving the gripper, while left_ego_image shows it falling outside the drawer and landing on the tabletop beside the cabinet. It remains there at frame 273 in left_ego_image; this is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 172 | No |
| 172 | 181 | Yes |
| 181 | 274 | No |

## Failure annotations

### Failure 1

- Frames: 172-181
- Categories: manipulation
- Explanation: After successfully transporting the spoon, the robot releases it outside the drawer: wrist_image shows it leaving the fingers at frames 172–174, and left_ego_image shows it falling in front of the cabinet at frames 174–178 and settling on the tabletop by frame 180. The established object control does not result in the intended placement.
- Recovery: Reacquire the spoon from the tabletop, verify a secure grasp, and position it fully over the open drawer interior before lowering and releasing it; verify that it remains inside. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The spoon lands on the tabletop beside the cabinet; no breakage, damage, or meaningful additional hazard is visible in frames 180–273 of left_ego_image.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop and the drawer remains open, so another acquisition and placement attempt can proceed without an environmental reset or human intervention.