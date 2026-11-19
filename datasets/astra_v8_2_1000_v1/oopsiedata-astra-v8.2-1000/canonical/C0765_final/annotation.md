# Episode: C0765

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left stuffed toy is blue and white, and the largest bowl is the central white bowl. The robot instead handles the pink toy on the right, lifts it in frames 55–62, and deposits it in the white bowl in frames 63–65. Frame 99 shows the blue-and-white target still on the table and the pink toy in the bowl, establishing wrong-object execution rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 11 | No |
| 11 | 66 | Yes |
| 66 | 100 | No |

## Failure annotations

### Failure 1

- Frames: 11-66
- Categories: sequencing_semantic
- Explanation: In image_primary frame 11, the gripper is visibly aligning over the right pink toy rather than the left blue-and-white toy. It continues handling the pink toy through frames 18–55, carries it toward the white bowl in frames 56–62, and releases it there in frames 63–65. This physically successful transfer uses the wrong object and leaves the requested target unmoved.
- Recovery: Return the pink toy to its original table area, then acquire the left blue-and-white toy and place it in the largest white bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The wrong stuffed toy is relocated, but image_primary frames 65 and 99 show no visible damage, overturned containers, or other meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: Restoring the original scene requires a straightforward relocation of the pink toy from the accessible white bowl to the table; no repair or difficult retrieval is indicated.