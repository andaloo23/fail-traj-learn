# Episode: C0407

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is blue-and-white and the largest bowl is the central white bowl. The robot instead lifts the pink toy (frames 15–20) and leaves it beside the orange container and white bowl (frames 63–65). It finally approaches and closes around the blue-and-white toy in frames 90–99, but no transfer to the bowl is visible. Completion is unconfirmed at the end; the earlier wrong-object handling is a visibly established failure.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 5 | No |
| 5 | 90 | Yes |
| 90 | 100 | No |

## Failure annotations

### Failure 1

- Frames: 5-90
- Categories: sequencing_semantic
- Explanation: In image_primary frames 5–14, the gripper targets and acquires the right-hand pink toy rather than the left blue-and-white toy. It lifts and carries the pink toy above the white bowl and toward the orange container (frames 15–58), releases it beside the containers (frames 59–65), and continues hovering or adjusting in that area through frame 89. This wrong-object sequence leaves the intended toy unmoved and does not accomplish the requested transfer.
- Recovery: Leave the pink toy safely supported, identify the originally left blue-and-white toy, grasp it securely, and place it inside the largest white bowl. Human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The unrelated stuffed toy is relocated on the tabletop, but image_primary frames 64–99 show no visible damage, spill, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The intended blue-and-white toy remains accessible and the white bowl remains usable; another task attempt needs no environmental intervention, although restoring the exact initial arrangement would require moving the pink toy back.