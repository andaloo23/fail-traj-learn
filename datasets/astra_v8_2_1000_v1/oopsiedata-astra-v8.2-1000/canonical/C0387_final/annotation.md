# Episode: C0387

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is the blue-and-white toy and the largest bowl is the central white bowl. The robot instead handles the pink toy on the right (frames 12–45), drops it outside the bowl (frames 46–47), and returns to it (frames 84–99). The intended left toy remains on the table and the white bowl remains empty at frame 99; this is visible noncompletion with wrong-object handling, not merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 12 | No |
| 12 | 46 | Yes |
| 46 | 48 | Yes |
| 48 | 84 | No |
| 84 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 12-46
- Categories: sequencing_semantic
- Explanation: In image_primary frames 12–22, the gripper aligns around and contacts the right pink toy rather than the left blue-and-white toy. It shifts the pink toy through frames 23–42 and lifts it in frames 43–45. Handling this visibly distinct wrong object does not advance the requested task.
- Recovery: Set the pink toy down safely, identify the left blue-and-white toy, and grasp that toy for transfer to the central white bowl; human intervention is not needed.
- Severity: low
- Severity evidence: The unrelated soft toy is displaced, but no damage or meaningful damage risk is visible.
- Resetability: minor_reset
- Resetability evidence: Restoring the displaced pink toy to its original position is a straightforward reset that can be performed by the robot or a person.

### Failure 2

- Frames: 46-48
- Categories: grasp
- Explanation: After the pink toy is visibly lifted in image_primary frames 44–45, it separates from the gripper and falls onto the table outside the white bowl in frames 46–47. This establishes failed retention during transport, independently of the wrong-object selection.
- Recovery: Leave the fallen toy safely supported or restore its position, then acquire the intended blue-and-white toy with a secure grasp before lifting; no human intervention is needed.
- Severity: low
- Severity evidence: The soft toy falls a short distance onto the tabletop and remains accessible; no damage is visible.
- Resetability: minor_reset
- Resetability evidence: The dropped toy can be repositioned with a simple tabletop pickup; no repair or difficult retrieval is required.

### Failure 3

- Frames: 84-100
- Categories: sequencing_semantic
- Explanation: In image_primary frames 84–90, the robot again lowers its gripper around the pink toy, then closes around and shifts it in frames 91–99 while the intended left toy remains untouched. This is another wrong-object attempt; the unfinished final acquisition does not independently establish a grasp failure.
- Recovery: Release the pink toy onto the table, redirect to the left blue-and-white toy, and transfer that toy into the largest white bowl; human intervention is not needed.
- Severity: low
- Severity evidence: Only further handling and displacement of the wrong soft toy are visible, with no observed damage.
- Resetability: minor_reset
- Resetability evidence: A simple release and repositioning of the pink toy would restore the affected scene; the intended toy and bowl remain usable.