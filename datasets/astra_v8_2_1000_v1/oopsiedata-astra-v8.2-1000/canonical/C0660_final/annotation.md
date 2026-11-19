# Episode: C0660

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is white and blue, and the largest bowl is the central white bowl. The robot instead displaces the pink toy during frames 22–31 and 53–73. It subsequently approaches and attempts to acquire the correct toy in frames 77–99, but no placement in the white bowl is visible; that bowl remains empty at frame 99. Completion is unconfirmed, and the final acquisition attempt is unfinished rather than conclusively failed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 22 | No |
| 22 | 32 | Yes |
| 32 | 53 | No |
| 53 | 74 | Yes |
| 74 | 100 | No |

## Failure annotations

### Failure 1

- Frames: 22-32
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary frames 22–27, the gripper engages and repositions the pink toy rather than the requested left white-and-blue toy. In frames 28–31 it withdraws empty while the pink toy remains on the table, establishing unsuccessful acquisition as well as wrong-object interaction.
- Recovery: Move clear of the pink toy, identify the left white-and-blue toy, and align the gripper around its body before acquiring and transferring it to the largest white bowl; human intervention is not needed.
- Severity: low
- Severity evidence: The unrelated soft toy is displaced on the tabletop, but no damage or meaningful damage risk is visible in image_primary frames 22–31.
- Resetability: immediate
- Resetability evidence: The intended toy and destination remain accessible and unchanged; the task can be reattempted without resetting the displaced pink toy.

### Failure 2

- Frames: 53-74
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary frames 53–69, the robot again engages the pink toy, pushing it toward the bottom of the image instead of acquiring the left white-and-blue toy. By frames 70–73 the gripper has withdrawn empty and the pink toy remains partly visible on the tabletop, confirming another unsuccessful acquisition of the wrong object.
- Recovery: Stop pursuing the pink toy, withdraw safely, and align with the white-and-blue toy on the left before lifting it into the largest white bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The pink toy is moved farther across the table, but no fall, damage, or other harmful consequence is visible; its partly cropped position does not establish that it fell.
- Resetability: immediate
- Resetability evidence: The requested toy and white bowl remain in place and accessible, allowing a new attempt without environmental intervention; restoring the pink toy's original pose is not necessary for the task.
