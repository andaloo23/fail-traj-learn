# Episode: C0514

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is blue-and-white, and the largest bowl is the central white bowl. The robot instead lifts the pink toy from the right/front at frames 21–24 and releases it into the white bowl at frames 35–36. At frame 55, the blue-and-white toy remains unmoved on the table. This is a visible wrong-object attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 6 | No |
| 6 | 39 | Yes |
| 39 | 56 | No |

## Failure annotations

### Failure 1

- Frames: 6-39
- Categories: sequencing_semantic
- Explanation: In image_primary frames 6–17, the gripper positions over and descends toward the pink toy rather than the left blue-and-white toy. It grasps the pink toy at frames 18–21, carries it to the white bowl at frames 22–34, and releases it at frames 35–36 before withdrawing at frames 37–38. Physical acquisition and placement succeed, but moving the wrong toy does not accomplish the requested task.
- Recovery: Return the pink toy to its original table position, then acquire the left blue-and-white toy and place it in the largest white bowl; no human intervention appears necessary.
- Severity: low
- Severity evidence: The wrong soft toy is relocated into an intact bowl; image_primary frames 36–55 show no visible damage or meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: Restoring the pink toy from the accessible white bowl to its original table position is a straightforward minor reset; the intended toy remains accessible and unmoved.