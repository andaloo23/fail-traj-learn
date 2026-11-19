# Episode: C0921

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is white and turquoise, and the largest bowl is the central white bowl. The robot first attempts to acquire the pink toy on the right (frames 11–53), then approaches and lifts the correct left toy (frames 84–99). At frame 99 the correct toy is still held beside the white bowl; placement is not visible. Completion is therefore unconfirmed, alongside an earlier visibly wrong-object attempt.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 11 | No |
| 11 | 54 | Yes |
| 54 | 100 | No |

## Failure annotations

### Failure 1

- Frames: 11-54
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary frames 11–50, the gripper repeatedly aligns with and closes around the right pink toy rather than the requested left turquoise-and-white toy. The pink toy moves during contact, but after the acquisition attempt the gripper withdraws empty while the pink toy remains on the table (frames 51–53), establishing unsuccessful acquisition as well as wrong-object selection. The requested toy remains untouched throughout this interval.
- Recovery: Withdraw clear of the pink toy, select the left turquoise-and-white toy, establish a secure grasp, and transfer it into the largest white bowl before releasing. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The wrong toy is slightly displaced on the tabletop, but image_primary frames 51–53 show no visible damage, overturned bowls, or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: Both toys and the destination bowl remain accessible and usable; the correct task can be reattempted without an environmental reset or human intervention.