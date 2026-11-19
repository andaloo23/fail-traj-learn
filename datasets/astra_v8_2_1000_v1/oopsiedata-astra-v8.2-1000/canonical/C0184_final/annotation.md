# Episode: C0184

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven starts open (frame 0, image and left_ego_image). The robot first displaces the unrelated green plate, then partially raises the oven door around frames 150–180. The door subsequently lowers and remains open at frame 246 (image and left_ego_image), establishing an unsuccessful closing attempt rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 30 | No |
| 30 | 119 | Yes |
| 119 | 196 | No |
| 196 | 247 | Yes |

## Failure annotations

### Failure 1

- Frames: 30-119
- Categories: collision
- Explanation: The gripper descends against the unrelated green plate and its contents, then slides the plate across the tabletop instead of closing the door (frames 30–118, wrist_image and left_ego_image). The plate's displacement is also visible in image; this is an unwanted scene interaction, not necessary oven-door contact.
- Recovery: Lift clear of the plate, locate the oven-door handle, and approach it without contacting the tableware; human intervention is not evidently required.
- Severity: low
- Severity evidence: The plate and its contents remain on the table with no visible breakage, spill, or meaningful damage.
- Resetability: immediate
- Resetability evidence: Although displaced, the plate remains supported and the oven is accessible; another closing attempt does not visibly require an environmental reset.

### Failure 2

- Frames: 196-247
- Categories: manipulation
- Explanation: After the robot has raised the door partway (frames 166–180, image and left_ego_image), the door reverses direction and lowers during frames 196–246, ending open rather than seated against the oven. The images establish failed door control but do not establish slipping or a mechanical cause.
- Recovery: Reposition at the handle and guide the door through its upward closing arc until seated, then verify it remains closed before withdrawing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The consequence is an open oven and an unsuccessful attempt; no damage to the door, appliance, or robot is visible.
- Resetability: immediate
- Resetability evidence: The door remains attached and accessible in an open position, allowing a new attempt without visible repair or manual resetting.