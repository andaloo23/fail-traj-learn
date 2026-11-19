# Episode: C0156

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is white and blue, and the largest bowl is the central white bowl. Instead, the robot acquires the pink-and-brown toy on the right (frames 16–29), carries it around the bowls, and releases it onto the table in front of the orange container (frames 77–78). At frame 99, the intended blue-and-white toy remains unmoved and the largest bowl remains empty; this is visible wrong-object behavior, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 15 | No |
| 15 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 15-100
- Categories: sequencing_semantic
- Explanation: In image_primary frame 15, the gripper visibly approaches the right pink-and-brown toy rather than the left blue-and-white toy. It grasps and lifts that wrong object in frames 22–29, carries it above and beside the white bowl and orange container in frames 30–76, then releases it onto the table in frames 77–78. Frames 83–99 show renewed engagement with the same wrong toy, while the intended toy remains untouched. This continuous wrong-object handling does not advance the stated task; successful lifting does not establish a physical grasp failure.
- Recovery: Leave the pink-and-brown toy safely supported on the table, withdraw, identify the original left blue-and-white toy, and transfer it into the central white bowl. Human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The wrong soft toy is relocated onto the tabletop, but image_primary frames 78–99 show no visible damage or meaningful damage risk; the bowls and intended toy remain usable.
- Resetability: immediate
- Resetability evidence: The intended toy and largest bowl remain accessible and unchanged in image_primary frame 99, so the correct task can be reattempted without a human reset.
