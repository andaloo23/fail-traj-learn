# Episode: C0651

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is blue-and-white and the largest bowl is the central white bowl. The robot first manipulates the unrelated pink-and-brown toy (frames 14–59), then picks up the left toy (frames 77–82), but releases it into the smaller orange container (frames 93–99). The white bowl remains empty at frame 99; this is a visibly incorrect placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 6 | No |
| 6 | 60 | Yes |
| 60 | 85 | No |
| 85 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 6-60
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary, the robot aligns over the right/front pink-and-brown toy at frame 6 and repeatedly handles it through frame 59 instead of acquiring the left blue-and-white toy. The wrong toy moves with the gripper briefly but is left on the table as the gripper rises empty at frames 29, 41, and 59, supporting unsuccessful retention as well as wrong-object selection. The unrelated toy is displaced and rotated.
- Recovery: Stop handling the unrelated toy, identify the originally left blue-and-white toy, and grasp it securely before transporting it to the central white bowl. Human intervention is not necessary for task recovery; restore the unrelated toy if the original scene arrangement is required.
- Severity: low
- Severity evidence: The plush toy is displaced on the tabletop, with no visible damage or meaningful damage risk in image_primary frames 29–59.
- Resetability: minor_reset
- Resetability evidence: Returning the unrelated toy to its original position and orientation requires only a straightforward repositioning; no repair or difficult retrieval is evident.

### Failure 2

- Frames: 85-100
- Categories: sequencing_semantic
- Explanation: After carrying the correct toy over the largest white bowl in image_primary frames 82–84, the robot moves away toward the smaller orange container starting at frame 85. It releases the toy into that container at frames 93–94 and withdraws through frame 99, leaving the intended bowl empty.
- Recovery: Reacquire the blue-and-white toy from the orange container, transport it over the central white bowl, and release it inside that bowl. No human intervention is visibly required.
- Severity: low
- Severity evidence: The toy is placed in the wrong container without visible damage, spillage, or hazardous contact.
- Resetability: immediate
- Resetability evidence: The toy remains accessible in the open orange container, so the robot can immediately attempt a corrective transfer without environmental intervention.