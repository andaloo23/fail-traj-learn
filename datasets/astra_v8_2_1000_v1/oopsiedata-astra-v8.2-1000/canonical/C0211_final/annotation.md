# Episode: C0211

## Episode annotation

- Language task: remove the blue cloth from the yellow block
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the first grasp closes near the cloth at frames 19–26, then moves away empty at frames 27–34 while the cloth remains in place. A renewed attempt at frames 49–69 catches and lifts an edge, but removal is not visibly completed before the recording ends. The yellow block remains obscured or indistinguishable; the final attempt is unfinished rather than demonstrably failed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 19 | No |
| 19 | 49 | Yes |
| 49 | 70 | No |

## Failure annotations

### Failure 1

- Frames: 19-49
- Categories: grasp
- Explanation: In right_shoulder_cam, the gripper closes at the cloth's front edge at frame 19 without securing it. The closed gripper subsequently lifts and shifts away empty at frames 27–34 while the cloth stays in place, confirming failed acquisition. It remains near the edge without acquiring or moving the cloth through frame 48; reopening and realignment begin at frame 49.
- Recovery: Reopen the gripper, align the fingers around an accessible cloth edge, secure a pinch, and verify that the cloth follows a small lift before pulling it clear of the block. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The missed acquisition leaves the cloth in place; no damage, displacement of unrelated objects, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The cloth remains available for another grasp and the environment requires no visible resetting or human intervention.