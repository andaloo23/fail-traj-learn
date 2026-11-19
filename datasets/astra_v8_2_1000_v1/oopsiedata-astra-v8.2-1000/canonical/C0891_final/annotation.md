# Episode: C0891

## Episode annotation

- Language task: Pack the toys onto the wooden tray.
- Success label: failure
- Outcome evidence: The robot moves the yellow banana-shaped object off the tray (frames 63–140, overhead_cam and wrist_cam), then successfully places the pink rabbit on it (frames 326–338, both cameras). However, its subsequent acquisition of the beige toy fails: the gripper closes short of it and moves away empty (frames 424–464, wrist_cam). At frame 566, both cameras show the rabbit on the tray but the beige toy still on the table, establishing incomplete packing rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 424 | No |
| 424 | 497 | Yes |
| 497 | 567 | No |

## Failure annotations

### Failure 1

- Frames: 424-497
- Categories: grasp
- Explanation: At frames 424–427, wrist_cam shows the fingers completing closure in empty space short of the beige toy. The robot then moves toward the tray without the toy, which remains on the table (frames 438–464, wrist_cam and overhead_cam), and opens its empty gripper over the tray at frames 489–496. This unsuccessful acquisition and empty transfer do not advance packing.
- Recovery: Reopen the gripper, realign its fingers around the beige toy, acquire it, and verify that it lifts with the gripper before transferring it onto the tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The beige toy remains on the tabletop; neither camera shows damage or a meaningful damage risk from the missed acquisition.
- Resetability: immediate
- Resetability evidence: The toy remains accessible and the tray remains usable, so another acquisition attempt requires no environmental reset or human intervention.