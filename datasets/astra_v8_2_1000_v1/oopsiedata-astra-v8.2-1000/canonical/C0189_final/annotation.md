# Episode: C0189

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left stuffed toy is the white-and-blue toy and the largest bowl is the central white bowl. The robot instead approaches and lifts the pink toy on the right (frames 8–21), releases it onto the table in front of the white bowl (frames 29–30), and engages that same toy again (frames 41–58). The intended left toy remains untouched through frame 58; this is visible wrong-object behavior, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 8 | No |
| 8 | 59 | Yes |

## Failure annotations

### Failure 1

- Frames: 8-59
- Categories: sequencing_semantic
- Explanation: In image_primary frame 8, the gripper is descending toward the right-hand pink toy rather than the left white-and-blue toy. It grasps and lifts the pink toy in frames 14–21, transports it toward the white bowl, and releases it outside the bowl in frames 29–30. Frames 41–58 show renewed engagement with the same wrong toy. This continuous wrong-object sequence never advances the requested transfer of the left toy; successful lifting of the pink toy does not constitute a grasp failure.
- Recovery: Release the pink toy safely onto a clear tabletop area if held, then approach and grasp the white-and-blue toy on the left, lift it clear of the surroundings, and place it inside the largest white bowl. Human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The wrong plush toy is relocated on the tabletop, and the white bowl shifts during the sequence, but image_primary frames 30–58 show no visible damage, spill, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The intended toy remains accessible on the table and the largest bowl remains upright and usable in image_primary frame 58; another task-directed attempt does not require a human environmental reset.