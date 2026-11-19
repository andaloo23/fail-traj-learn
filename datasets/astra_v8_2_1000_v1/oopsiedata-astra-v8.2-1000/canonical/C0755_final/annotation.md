# Episode: C0755

## Episode annotation

- Language task: Pack the cups with a single arm.
- Success label: failure
- Outcome evidence: In base_image, the robot approaches the clustered cups (frames 18–49), manipulates them, and visibly lifts a cup assembly (frames 114–118). During subsequent movement, the neighboring blue cup tips and rolls onto its side (frames 120–129). At frame 146, cups remain on the tabletop and none are visibly packed into the box at the right. Packing completion is unconfirmed, while the toppling is a visibly unsuccessful side effect.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 120 | No |
| 120 | 147 | Yes |

## Failure annotations

### Failure 1

- Frames: 120-147
- Categories: collision
- Explanation: In base_image, movement of the held cup assembly against the neighboring blue cup starts tipping it at frame 120; it falls onto its side and rolls left by frames 126–129. The robot then continues moving the held cups leftward beside and against the fallen cup through frames 131–146, further displacing it rather than packing the cups. This is visible disruptive contact; no hidden cause or damage is established.
- Recovery: Stop lateral pushing, lift the held cups clear of the fallen cup, and place them securely in the packing destination; then reacquire and reorient the fallen cup before packing it. Human intervention is not evidently necessary.
- Severity: low
- Severity evidence: The blue cup topples and moves across the tabletop, but no breakage, spilled contents, or other meaningful damage is visible in base_image frames 120–146.
- Resetability: minor_reset
- Resetability evidence: Returning the fallen cup to its previous standing orientation requires a straightforward repositioning; it remains accessible on the tabletop, with no repair or difficult retrieval visibly needed.