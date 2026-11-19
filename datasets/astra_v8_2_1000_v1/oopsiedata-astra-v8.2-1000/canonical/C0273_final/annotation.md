# Episode: C0273

## Episode annotation

- Language task: Move the hammer to the plate. Then, grasp the mushroom.
- Success label: failure
- Outcome evidence: In image_primary, the robot acquires and transports the hammer in frames 37–44, but pushes the plate away during frames 45–52 and leaves the hammer beside rather than on it, visible in frames 62–64. It subsequently grasps and lifts the pink-handled spoon in frames 96–110 instead of the mushroom. The mushroom remains untouched through frame 119; this is visibly incorrect execution, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 45 | No |
| 45 | 55 | Yes |
| 55 | 73 | No |
| 73 | 120 | Yes |

## Failure annotations

### Failure 1

- Frames: 45-55
- Categories: manipulation, collision
- Explanation: In image_primary frames 45–52, the held hammer/gripper moves against the plate edge and pushes the plate toward the lower right instead of placing the hammer inside it. The gripper opens in frames 52–54; subsequent clearance in frames 58–64 reveals the hammer resting on the tabletop beside the displaced plate. The exact contacting component is partly obscured.
- Recovery: Re-localize the displaced plate and hammer, reacquire the hammer, lift it clear of the rim, and place it inside the plate before proceeding to the mushroom; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The plate is displaced and placement fails, but image_primary frames 55–64 show no breakage, spill, or other meaningful damage.
- Resetability: immediate
- Resetability evidence: The hammer and plate remain accessible on the tabletop, allowing another attempt using their updated positions without a required environmental reset.

### Failure 2

- Frames: 73-120
- Categories: sequencing_semantic
- Explanation: In image_primary frames 73–95, the robot approaches and aligns with the pink-handled spoon on the left, rather than the mushroom on the right. Frames 96–110 establish successful acquisition and transport of that wrong object, followed by lowering it beside the hammer in frames 115–119. This does not perform the requested mushroom grasp.
- Recovery: Safely set down and release the spoon, correct the hammer placement if still needed, then approach and grasp the mushroom; no human intervention is visibly required.
- Severity: low
- Severity evidence: An unrelated utensil is moved, but no damage or meaningful damage risk is established in image_primary frames 96–119.
- Resetability: immediate
- Resetability evidence: The spoon can be safely released on the accessible tabletop and the intended objects remain available; no human reset or repair is visibly needed.